%% CES surface enneigée
% *Author: Simon Gascoin (CNRS/CESBIO)*
% 
% *June 2015*
%
% This code is a demonstrator of the snow detection algorithm for
% Sentinel-2 images. It calls <S2snow.html the function S2snow> using 
% subsets of SPOT-4 or Landsat-8 level 2 images
%
% The input files were generated from L2 images downloaded from Theia Land
% and pre-processed by three shell scripts:
%
% #  |decompresse_*.sh|,
%        to unzip the files
% #  |decoupe_*.sh|,
%        to extract a rectangle AOI from L2A data using
%       gdal_translate with projection window defined in the ascii file
%       _AOI_test_CESNeige.csv_
% #  |projette_mnt_*.sh|,
%        to project the SRTM DEM and resample at 30m or 20m
%       (Landsat8 or Take5) over the same AOI. It uses gdalwarp with the 
%       cubicspline option

%%
% Check Matlab version
matlabversion=version;
assert(str2double(matlabversion(end-5:end-2))>=2014,...
    'Needs Matlab version 2014 and later')

%% Configuration
% This demo can run for only one image (option 1) or process several
% images series from different sites and sensors (option 2)

demotype=1;

%%
% If this flag QL is true the code will output three figures for each image
%
% # a bar graph showing the snow fraction per elevation band,
% # a bar graph showing the snow, cloud and elevation area in m2,
% # a false color composite image overlaid by snow and cloud masks.

QL=true;

%%
% Define the output path for the figures

pout='../figures/demo_CESneige';

%%
% Define a label to add to the figure file names

label='ndsipass2_015_cloudpass1';

%% Cloud mask processing parameters
% Resampling factor to determine the "dark clouds" in the initial cloud
% mask. Here rf=8 corresponds to a target resolution of 240m for Landsat.

rf=8;

%%
% Dark cloud threshold (reflectance unit: per mil). The clouds pixels with a (coarse) reflectance lower than rRed_darkcloud
% are selected to pass the snow test 

rRed_darkcloud=500;

%%
%  
% Back to cloud threshold. Pixels which are not detected as snow then they go back to the cloud
% mask only if their reflectance at full resolution is greater than
% rRed_backtocloud. Here we use full resolution reflectances because
% resampled cloud pixels reflectance drops rapidly along the cloud edges
% due to the mixing with the land reflectance.

rRed_backtocloud=100;

%% Snow detection parameters
%
% Elevation band height in m. 
dz=100;
%%
% NDSI threshold for pass 1 
ndsi_pass1=0.4;
%%
% Threshold in the red reflectance for pass 1
rRed_pass1=200;
%%
% NDSI threshold for pass 2 
ndsi_pass2=0.15; % Note: Zhu's fmask algorithm uses 0.15
%%
% Threshold in the red reflectance for pass 2
rRed_pass2=120;
%%
% Minimum snow fraction from which to compute the snowline elevation (zs)
fsnow_lim=0.1;
%%
% Snow fraction limit to go to pass 2.
% The total snow fraction after pass 1 is computed to decide 
% whether or not proceed to pass 2. If the snow fraction is below
% fsnow_total_lim then pass 2 is skipped because the number of snow pixels
% is not sufficient to properly determine the snow line elevation. Here we
% use 1000 pixels.
fsnow_total_lim=0.001; % Warning! it depends on the image size

%% Definition of the input images 
switch demotype
    case 1 
        %% 
        % use only 1 image
        satlist={'Take5'};
        sitelist{1}={'Maroc'};
        datelist{1}{1}={'20130327'}; % format yyyymmdd
    case 2 
        %% 
        % process a batch of 2 x Landsat8 and 4 x Take5 images series
        [satlist,sitelist,datelist]=load_demo_input('all');
    otherwise
        error('demotype should be 1 or 2')
end

%% Data loading
% Begin the sensor loop
nsat=length(satlist);
for isat=1:nsat 
    
    sat=satlist{isat};
    
    nsite=length(sitelist{isat});

    %%
    % Get the sensor band numbers and no-data value
    switch sat
        case 'Take5'
            nGreen=1; % Index of green band
            nMIR=4; % Index of SWIR band (1 to 3 µm) = band 11 (1.6 µm) in S2
            nRed=2; % Index of red band
            nodata=-10000; % no-data value
        case 'Landsat8'
            nGreen=3;
            nMIR=6;
            nRed=4;
            nodata=-10000;
        otherwise
            error('sat should be Take5 or Landsat8')
    end
    %%
    % Begin the site loop
    for isite=1:nsite;  

        site=sitelist{isat}{isite};
        ndate=length(datelist{isat}{isite});
        
        %%
        % read SRTM DEM for this site
        fdem=['../' sat '/AOI_test_CESNeige/SRTM/' site '/' site '.tif'];
        [Zdem,R]=geotiffread(fdem);
        
        %%
        % Begin the date loop
        for idate=1:ndate 

            date=datelist{isat}{isite}{idate};
            
            %%
            % Read the L2 reflectance data (search the image filename based on the date)
            pL2=['../' sat '/AOI_test_CESNeige/LEVEL2A/' site]; % path
            fL2=dir([pL2 '/*' date '*PENTE*.TIF']); % file list
            assert(~isempty(fL2),'The L2 image is not present in the input directory')
            f=[pL2 '/' fL2.name];
            [ZL2,~]=geotiffread(f);
            
            %%
            % The data are converted to double because it enables to work
            % with NaN, but we could probably avoid this to optimize memory use..
            ZL2=double(ZL2);
            ZL2(ZL2==nodata)=NaN;
            
            %%
            % Read the cloud mask
            fc=dir([pL2 '/*' date '*NUA.TIF']);
            assert(~isempty(fc),'The cloud mask is not present in the input directory')
            f=[pL2 '/' fc.name];
            [Zc,~]=geotiffread(f);
            
            %% Snow detection 
            % Calls <S2snow.html the function S2snow>
            [snowtest,cloudtestfinal,z_center,B1,B2,fsnow,zs,...
                fsnow_z,fcloud_z,N,z_edges]...
                = S2snow(...
                ZL2,Zc,Zdem,nGreen,nRed,nMIR,rf,QL,rRed_darkcloud,...
                ndsi_pass1,ndsi_pass2,rRed_pass1,rRed_pass2,dz,fsnow_lim,...
                fsnow_total_lim,rRed_backtocloud);
            
            %% Figures
            if QL
                
                %%
                % Draw a bar plot of the snow fraction per elevation band
                figure(1),clf
                barh(z_center,fsnow_z,1,'facecolor','c');
                hold on
                if ~isempty(zs)
                    hrf=refline(0,zs);
                    set(hrf,'Color','r','LineStyle','--','LineWidth',2)
                end
                xlabel('Fractional area')
                ylabel('Elevation (m)')
                legend('Snow','zs')
                title(sprintf('%s zs=%g',date,zs))
                
                %%
                % Draw a bar plot of the snow area and elevation band area
                figure(2),clf
                [Nz,~,~] = histcounts(Zdem(:),z_edges);
                barh(z_center,Nz,1,'facecolor',.8*[1 1 1]);
                hold on
                barh(z_center,(fcloud_z+fsnow_z).*Nz',1,'facecolor',.5*[1 1 1]);
                barh(z_center,fsnow_z.*Nz',1,'facecolor','c');
                if ~isempty(zs)
                    hrf=refline(0,zs);
                    set(hrf,'Color','r','LineStyle','--','LineWidth',2)
                end
                xlabel('Area (m2)')
                ylabel('Elevation (m)')
                legend('DEM','Cloud','Snow','zs')
                title(sprintf('%s zs=%g',date,zs))
                
                %%
                % Show an RGB composition overlaid with pass 1 and 2 snow cover
                % polygons. The clouds pixels are in black.
                figure(3),clf
                z=ZL2(:,:,[nMIR nRed nGreen]);
                max_b=[300 300 300];
                z2=zeros(size(z),'uint8');
                for b=1:3
                    z2(:,:,b)=~cloudtestfinal.*double(z(:,:,b))/max_b(b)*255;
                end
                imshow(uint8(z2),'Border','tight')
                hold on
                for k = 1:length(B1)
                    boundary = B1{k};
                    %         if length(boundary)>100
                    plot(boundary(:,2), boundary(:,1), 'y', 'LineWidth', 1)
                    %         end
                end
                if ~isempty(zs)
                    for k = 1:length(B2)
                        boundary = B2{k};
                        %         if length(boundary)>100
                        plot(boundary(:,2), boundary(:,1), 'm', 'LineWidth', 1)
                        %         end
                    end
                end
                
                %%
                % Print figures
                set(1:3,'PaperPositionMode','auto','Visible','off');
                pfig=[pout '/' sat '/' site];
                system(sprintf('mkdir -p %s/zs1',pfig));
                system(sprintf('mkdir -p %s/zs2',pfig));
                system(sprintf('mkdir -p %s/QL',pfig));
                f1=sprintf('%s/zs1/%s_%s_%s_%s.png',pfig,sat,site,date,label);
                f2=sprintf('%s/zs2/%s_%s_%s_%s.png',pfig,sat,site,date,label);
                f3=sprintf('%s/QL/%s_%s_%s_%s.png',pfig,sat,site,date,label);
                print(1,f1,'-dpng')
                print(2,f2,'-dpng')
                print(3,f3,'-dpng')
                
            end
        end
        
    end
    
end
