import numpy as np
import requests
from io import BytesIO
from PIL import Image
from astropy.io import fits
from PyQt6.QtCore import QThread, pyqtSignal

class Inspection:
    SURVEY_LAYERS = {
        'dr9':  'ls-dr9',
        'dr10': 'ls-dr10-grz',
        'dr11': 'ls-dr11',
    }

    def __init__(self,main_window):
        self.main_window = main_window

        self.idx_to_band_dict = {0:'g',1:'r',2:'z'}

        self.inspection_parameters = self.main_window.inspection_parameters
        self.dr_version = 'dr10'
        self.layer = self.SURVEY_LAYERS[self.dr_version]
        self.inspection_parameters['survey'] = 'Legacy Survey DR10'
        self.ra_col_name, self.dec_col_name = self.inspection_parameters['ra column name'],self.inspection_parameters['dec column name']
        self.cutout_size = 101
        self.pixscale = 0.262  # arcsec per pixel
        self.simulation_mode = False
        self.cached_images_idxs = []
        self.cached_images = {}

        self.df_has_been_modified = False

    def set_survey(self, dr_version):
        """Switch the cutout source and clear the image cache."""
        dr = dr_version.lower()
        self.dr_version = dr
        self.layer = self.SURVEY_LAYERS.get(dr, 'ls-dr10-grz')
        self.inspection_parameters['survey'] = f'Legacy Survey {dr.upper()}'
        self.cached_images.clear()
        self.cached_images_idxs.clear()

    @staticmethod
    def _is_blank(arr):
        """True if the array is uniform (all-zero / all-one etc.) — out-of-footprint cutout."""
        if arr is None:
            return True
        flat = arr.ravel().astype(float)
        return float(flat.max()) - float(flat.min()) < 1e-4

    @staticmethod
    def _is_valid_coord(val):
        try:
            f = float(val)
            return f == f  # False for NaN
        except (TypeError, ValueError):
            return False

    def get_current_images(self, idx):
        self.current_idx = idx

        ra = self.main_window.df[self.ra_col_name].values[idx]
        dec = self.main_window.df[self.dec_col_name].values[idx]

        if not self._is_valid_coord(ra) or not self._is_valid_coord(dec):
            return (
                {'rgb': False, 'grz': False, 'bad_coords': True},
                {'rgb': None, 'grz': None, 'ra_val': str(ra), 'dec_val': str(dec)},
            )

        if self.is_cached(self.current_idx):
            print(f'{self.current_idx} pulled from cache')
            rgb_success, rgb_cutout, grz_success, grz_cutout = self.pull_from_cache(idx=self.current_idx)

        else:
            print(f'{self.current_idx} pulled web')

            rgb_success, rgb_cutout = self.get_rgb_cutout(ra=ra, dec=dec, cutout_size=self.cutout_size, _simulation = self.simulation_mode)
            grz_success, grz_cutout = self.get_grz_cutout(ra=ra, dec=dec, cutout_size=self.cutout_size, _simulation = self.simulation_mode)

            if rgb_success and grz_success:
                self.add_to_cache(list_of_new_images=[rgb_cutout,grz_cutout],idx=self.current_idx)

        return {'rgb': rgb_success, 'grz': grz_success, 'bad_coords': False}, {'rgb': rgb_cutout, 'grz': grz_cutout}
    
    def get_current_url(self):
        ra, dec = self.main_window.df[self.ra_col_name].values[self.current_idx], self.main_window.df[self.dec_col_name].values[self.current_idx]
        url='https://www.legacysurvey.org/viewer?ra={}&dec={}&layer={}&pixscale=0.26&size=101&zoom=16'.format(ra,dec,self.layer)
        return url
    
    def get_current_metadata(self):
        ra=self.main_window.df[self.ra_col_name].values[self.current_idx]
        dec=self.main_window.df[self.dec_col_name].values[self.current_idx]
        survey=self.inspection_parameters['survey']
        grader_name=self.inspection_parameters['grader name']

        user_selected_more_data= True if type(self.inspection_parameters['additional columns'])==list else False

        if user_selected_more_data:
            extra_metadata={}
            for var in self.inspection_parameters['additional columns']:
                extra_metadata[var]=self.main_window.df[var].values[self.current_idx]
        else:
            extra_metadata=None

        return {'ra':ra,'dec':dec,'survey':survey,'user selected data':extra_metadata, 'grader name':grader_name}

    def get_current_comment_and_grade(self):
        grade=self.main_window.df[self.inspection_parameters['grader name']+'_grades'].values[self.current_idx]
        comment=self.main_window.df[self.inspection_parameters['grader name']+'_comments'].values[self.current_idx]
        return {'grade':grade, 'comment':comment}
    
    def update_df(self,comment_and_grade):
        self.main_window.df.loc[self.current_idx, self.inspection_parameters['grader name']+'_grades'] = comment_and_grade['grade']
        self.main_window.df.loc[self.current_idx, self.inspection_parameters['grader name']+'_comments'] = comment_and_grade['comment']


    def get_grz_cutout(self,ra, dec, cutout_size=101, _simulation = False):
        if not _simulation:
            url = 'https://www.legacysurvey.org/viewer/cutout.fits?ra={}&dec={}&layer={}&pixscale={}&size={}&zoom=16'.format(ra, dec, self.layer, 0.262, int(cutout_size))
            try:
                data = fits.open(url)[0].data
                data = np.flip(data, axis=2)           # flip L-R
                data = np.rot90(data, k=1, axes=(1,2))  # rotate 90° CCW
                return True, data
            except:
                return False, None
        else:
            print('***WARNING***\nData acquisition in simulation mode')
            try:
                return(np.load('test_data/0_grz.npy'))
            except:
                return None

    def get_rgb_cutout(self,ra, dec, cutout_size=101, _simulation = False):
        url = 'https://www.legacysurvey.org/viewer/cutout.jpg?ra={}&dec={}&layer={}&pixscale={}&size={}&zoom=16'.format(ra, dec, self.layer, 0.262, int(cutout_size))
        if not _simulation:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    image_buffer = BytesIO(response.content)
                    image = Image.open(image_buffer)
                    return True, np.rot90(np.array(image), k=-1)
                else:
                    return False, None
            except:
                return False, None
        else:
            print('***WARNING***\nData acquisition in simulation mode')
            try:
                return np.load('test_data/0_rgb.npy')
            except:
                return None
            
    def is_cached(self,new_idx):
        if new_idx in self.cached_images_idxs:
            return True
        else:
            return False
        
    def add_to_cache(self,list_of_new_images,idx,rgb=True,grz=True):
        self.cached_images['{}rgb'.format(idx)]=np.copy(list_of_new_images[0])
        self.cached_images['{}grz'.format(idx)]=np.copy(list_of_new_images[1])
        self.cached_images_idxs.append(idx)
        print(f'{idx} added to cache')

    def pull_from_cache(self,idx):
        rgb_cutout = self.cached_images['{}rgb'.format(idx)]
        grz_cutout = self.cached_images['{}grz'.format(idx)]
        rgb_success, grz_success = True, True
        return rgb_success, rgb_cutout, grz_success, grz_cutout

class PrefetchThread(QThread):
    fetched = pyqtSignal(object, object, int, str)  # rgb, grz, idx, layer

    def __init__(self, inspection, idx):
        super().__init__()
        self.inspection = inspection
        self.idx = idx
        self.layer_snapshot = inspection.layer

    def run(self):
        try:
            df = self.inspection.main_window.df
            ra = df[self.inspection.ra_col_name].values[self.idx]
            dec = df[self.inspection.dec_col_name].values[self.idx]
            rgb_ok, rgb = self.inspection.get_rgb_cutout(ra, dec, self.inspection.cutout_size)
            grz_ok, grz = self.inspection.get_grz_cutout(ra, dec, self.inspection.cutout_size)
            if rgb_ok and grz_ok:
                self.fetched.emit(rgb, grz, self.idx, self.layer_snapshot)
        except Exception as e:
            print(f'[Prefetch] idx={self.idx} failed: {e}')