import numpy as np
import requests
from io import BytesIO
from PIL import Image
from astropy.io import fits
from PyQt6.QtCore import QThread, pyqtSignal

class Inspection:
    SURVEY_LAYERS = {
        'dr9':  'ls-dr9-grz',
        'dr10': 'ls-dr10-grz',
        'dr11': 'ls-dr11-grz',
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
    
    def get_current_images(self, idx):
        self.current_idx = idx

        if self.is_cached(self.current_idx):
            print(f'{self.current_idx} pulled from cache')
            rgb_success, rgb_cutout, grz_success, grz_cutout = self.pull_from_cache(idx=self.current_idx)

        else:
            print(f'{self.current_idx} pulled web')

            ra, dec = self.main_window.df[self.ra_col_name].values[idx], self.main_window.df[self.dec_col_name].values[idx]

            rgb_success, rgb_cutout = self.get_rgb_cutout(ra=ra, dec=dec, cutout_size=self.cutout_size, _simulation = self.simulation_mode)
            grz_success, grz_cutout = self.get_grz_cutout(ra=ra, dec=dec, cutout_size=self.cutout_size, _simulation = self.simulation_mode)

            if rgb_success and grz_success:
                self.add_to_cache(list_of_new_images=[rgb_cutout,grz_cutout],idx=self.current_idx)

        return {'rgb':rgb_success,'grz':grz_success},{'rgb':rgb_cutout,'grz':grz_cutout}
    
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

    # def queue_images(self):
    #     prev_next_ras, prev_next_decs, prev_next_idxs = [], [], []

    #     if not self.is_cached(self.current_idx+1):
    #         prev_next_ras.append(self.main_window.df[self.ra_col_name].values[self.current_idx+1])
    #         prev_next_decs.append(self.main_window.df[self.ra_col_name].values[self.current_idx+1])
    #         prev_next_idxs.append(self.current_idx+1)

    #     if not self.is_cached(self.current_idx-1):
    #         prev_next_ras.append(self.main_window.df[self.ra_col_name].values[self.current_idx-1])
    #         prev_next_decs.append(self.main_window.df[self.ra_col_name].values[self.current_idx-1])
    #         prev_next_idxs.append(self.current_idx-1)

    #     if len(prev_next_ras)>0:
    #         cache_fetcher = ThreadImageFetcher(ra=prev_next_ras,dec=prev_next_decs,idxs=prev_next_idxs,inpection_class = self)
    #         cache_fetcher.output.connect(lambda thread_output: self.add_to_cache(list_of_new_images=thread_output[:2],idx=thread_output[2]))
    #         cache_fetcher.start()

    def get_grz_cutout(self,ra, dec, cutout_size=101, _simulation = False):
        if not _simulation:
            url = 'https://www.legacysurvey.org/viewer/cutout.fits?ra={}&dec={}&layer={}&pixscale={}&size={}&zoom=16'.format(ra, dec, self.layer, 0.262, int(cutout_size))
            try:
                return True, fits.open(url)[0].data
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
            response = requests.get(url)

            if response.status_code == 200:
                image_buffer = BytesIO(response.content)
                image = Image.open(image_buffer)
                return True, np.array(image)
            else:
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
        self.cached_images_idxs.append(self.current_idx)
        print(f'{idx} added to cache')

    def pull_from_cache(self,idx):
        rgb_cutout = self.cached_images['{}rgb'.format(idx)]
        grz_cutout = self.cached_images['{}grz'.format(idx)]
        rgb_success, grz_success = True, True
        return rgb_success, rgb_cutout, grz_success, grz_cutout

# class CSVSaver(QThread):

class ThreadImageFetcher(QThread):
    output = pyqtSignal(list)
    def __init__(self,ra,dec,idxs,inspection_class):
        super().__init__()
        self.ra, self.dec, self.idxs,self.inspection_class = ra, dec, idxs, inspection_class

    def run(self):
        for ra, dec, idx in zip(self.ra, self.dec,self.idxs):

            rgb_success, rgb_cutout = self.inspection_class.get_rgb_cutout(ra=ra, dec=dec, cutout_size=self.inspection_class.cutout_size, _simulation = self.inspection_class.simulation_mode)
            grz_success, grz_cutout = self.inspection_class.get_grz_cutout(ra=ra, dec=dec, cutout_size=self.inspection_class.cutout_size, _simulation = self.inspection_class.simulation_mode)

            if rgb_success and grz_success:
                self.output.emit([rgb_cutout,grz_cutout,idx])