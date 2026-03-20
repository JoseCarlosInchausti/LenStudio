class ImageData:
    def __init__(self, df):
        self.df = df
        self.saved_fits={}
        self.saved_npy={}
        self.saved_redshifts={}
    
    def update_image(self,i):
        self.current_index=i
        self.stored_idxs = list(self.saved_fits.keys())

        if self.current_index not in self.stored_idxs:
            try:
                ra, dec = self.df['ra'].iloc[self.current_index], self.df['dec'].iloc[self.current_index]
            except:
                ra, dec = self.df['Ra'].iloc[self.current_index], self.df['Dec'].iloc[self.current_index]

            npy_array,hsc = get_cutout_by_radec_hsc(ra, dec)

            if hsc:
                # Get z with cutout size 147
                z_df = self.get_redshifts(ra,dec,cutout_size=147)
                fits_array = get_fits_cutout_by_radec_hsc(ra, dec)
            else:
                # Get z with cutout size 101
                z_df = self.get_redshifts(ra,dec,cutout_size=101)
                fits_array = get_fits_cutout_by_radec(ra, dec)

            self.saved_fits[self.current_index] = np.copy(fits_array)
            self.saved_npy[self.current_index] = (np.copy(npy_array), hsc)
            self.saved_redshifts[self.current_index] = z_df.copy()

        return self.saved_fits[self.current_index], self.saved_npy[self.current_index][0], self.saved_npy[self.current_index][1], self.saved_redshifts[self.current_index]

    def prepare_neighbor_data(self,neighbor_i):
        self.lock = threading.Lock()  # Thread-safe cache
        with self.lock:
            self.stored_idxs = list(self.saved_fits.keys())

        # If neighbor data aready exists
        if neighbor_i in self.stored_idxs:
            return
        else:
            try:
                ra, dec = self.df['ra'].iloc[self.current_index], self.df['dec'].iloc[self.current_index]
            except:
                ra, dec = self.df['Ra'].iloc[self.current_index], self.df['Dec'].iloc[self.current_index]

            npy_array,hsc = get_cutout_by_radec_hsc(ra, dec)

            if hsc:
                # Get z with cutout size 147
                z_df = self.get_redshifts(ra,dec,cutout_size=147)
                fits_array = get_fits_cutout_by_radec_hsc(ra, dec)
            else:
                # Get z with cutout size 101
                z_df = self.get_redshifts(ra,dec,cutout_size=101)
                fits_array = get_fits_cutout_by_radec(ra, dec)

            with self.lock: 
                self.saved_fits[self.current_index] = np.copy(fits_array)
                self.saved_npy[self.current_index] = (np.copy(npy_array), hsc)
                self.saved_redshifts[self.current_index] = z_df.copy()

                if neighbor_i-1 in self.stored_idxs:
                    del self.saved_fits[neighbor_i-1]
                    del self.saved_npy[neighbor_i-1]
                    del self.saved_redshifts[neighbor_i-1]
                if neighbor_i+1 in self.stored_idxs:
                    del self.saved_fits[neighbor_i+1]
                    del self.saved_npy[neighbor_i+1]
                    del self.saved_redshifts[neighbor_i+1]

    
    def get_redshifts(self,ra,dec,cutout_size):
        diff = 0.262*cutout_size/2/3600
        cat_url = "https://www.legacysurvey.org/viewer-desi/desi-spec-daily/1/cat.json?ralo={}&rahi={}&declo={}&dechi={}".format(ra-diff,ra+diff,dec-diff,dec+diff)
        cat_dict = eval(requests.get(cat_url, auth=('desi', '[REDACTED]')).content)
        
        if len(cat_dict) == 1:
            return None
        else:
            coordinates = np.array(cat_dict['rd'])
            ras, decs = coordinates[:,0],coordinates[:,1]
            redshifts = []
            for item in cat_dict['name']:
                if 'ZWARN' in item:
                    redshifts.append(item.split(' ')[-2]+'\nZWARN')
                elif 'STAR' in item:
                    redshifts.append('STAR')
                else:
                    # print(item)
                    redshifts.append(str(round(float(item.split(' ')[-1]),3)))
            return pd.DataFrame({'ra':ras,'dec':decs,'z':redshifts})
    

ImageDataHolder = ImageData(df)

def update_image(index):
    with output:
        output.clear_output(wait=True)
        try:
            ra, dec = df['ra'].iloc[index], df['dec'].iloc[index]
        except:
            ra, dec = df['Ra'].iloc[index], df['Dec'].iloc[index]
        
        fits_array, npy_array, hsc, redshifts_df = ImageDataHolder.update_image(index)

        fig, axs = plt.subplots(2, 5, figsize=(25, 10))  # 2 rows

        # --- Top row ---
        axs[0, 0].imshow(np.flipud(npy_array), origin='lower')
        if hsc:
            axs[0, 0].set_title('HSC RGB Image')
        else:
            axs[0, 0].set_title('RGB Image')
        axs[0, 0].axis('off')

        plot_cutout_with_redshifts(ax=axs[0, 1], rgb_cutout=npy_array, ra=ra, dec=dec, hsc=hsc,redshifts_df=redshifts_df)

        if hsc:
            cx,cy = 74,74

        else:
            cx,cy = 51,51
            

        # G band with circle
        zscale = ZScaleInterval()
        vmin_g, vmax_g = zscale.get_limits(fits_array[0])
        axs[0, 2].imshow(fits_array[0], origin='lower', cmap='gray', vmin=vmin_g, vmax=vmax_g * slider_g.value)
        axs[0, 2].set_title('G Band')
        axs[0, 2].axis('off')
        axs[0, 2].scatter(cx, cy, marker='o', facecolors='none', edgecolor='red')

        # R band with circle
        zscale = ZScaleInterval()
        vmin_r, vmax_r = zscale.get_limits(fits_array[1])
        axs[0, 3].imshow(fits_array[1], origin='lower', cmap='gray', vmin=vmin_r, vmax=vmax_r * slider_r.value)
        axs[0, 3].set_title('R Band')
        axs[0, 3].axis('off')
        axs[0, 3].scatter(cx, cy, marker='o', facecolors='none', edgecolor='red')

        # Z band with circle
        zscale = ZScaleInterval()
        vmin_z, vmax_z = zscale.get_limits(fits_array[2])
        axs[0, 4].imshow(fits_array[2], origin='lower', cmap='gray', vmin=vmin_z, vmax=vmax_z * slider_z.value)
        axs[0, 4].set_title('Z Band')
        axs[0, 4].axis('off')
        axs[0, 4].scatter(cx, cy, marker='o', facecolors='none', edgecolor='red')

        # --- Bottom row: G, R, Z only, NO circle ---
        for i, (band, vmin, vmax, slider, title) in enumerate(
            zip([fits_array[0], fits_array[1], fits_array[2]],
                [vmin_g, vmin_r, vmin_z],
                [vmax_g, vmax_r, vmax_z],
                [slider_g, slider_r, slider_z],
                ['G Band (no circle)', 'R Band (no circle)', 'Z Band (no circle)'])
        ):
            ax = axs[1, i+2]  # columns 2,3,4
            ax.imshow(band, origin='lower', cmap='gray', vmin=vmin, vmax=vmax * slider.value)
            ax.set_title(title)
            ax.axis('off')

        # Leave the first two bottom-row axes empty for alignment
        axs[1, 0].axis('off')
        axs[1, 1].axis('off')

        plt.tight_layout()
        plt.show()

        update_title(index)
        url = 'https://www.legacysurvey.org/viewer-desi/?ra={}&dec={}&layer=ls-dr10-grz&pixscale=0.26&size=101&zoom=16'.format(ra, dec)
        url_display.value = f'<a href="{url}" target="_blank">Open on Sky Viewer</a>'