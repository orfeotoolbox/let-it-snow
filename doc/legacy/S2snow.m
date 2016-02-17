%% Function S2snow
% *Author: Simon Gascoin (CNRS/CESBIO)*
%
% *June 2015*
%
% This function computes the snow presence and absence (snow/no-snow) from
% a high-resolution optical multispectral image like Sentinel-2
% (eg Landsat-8, SPOT-4)
% The input are the full resolution reflectances corrected from atmospheric
% and slope effects (Level 2A), the associated cloud mask and a digital
% elevation model.
% The output is a mask with three classes: snow/no-snow/cloud. The output cloud
% mask is different from the input cloud mask.
%
% The snow detection algorithm works in two passes: first the most evident
% snow is detected using a set of conservative thresholds, then this snow pixels
% are used to determine the lower elevation of the snow cover. A second pass
% is performed for the pixels above this elevation with a new set of less
% conservative thresholds
%
% The snow detection is made on a pixel-basin using the Normalized Difference Snow Index (NDSI):
%
% $$ \textrm{NDSI} = \frac{\rho_\textrm{{Green}}-\rho_\textrm{{MIR}}}{\rho_\textrm{{Green}}+\rho_\textrm{{MIR}}} $$
%
% where $\rho_\textrm{{Green}}$ is the reflectance in the green channel and $\rho_\textrm{{Green}}$ in the
% shortwave infrared.

%% Function call
function [snowtest,cloudtestfinal,z_center,B1,B2,fsnow,zs,...
    fsnow_z,fcloud_z,N,z_edges]...
    = S2snow(...
    ZL2,Zc,Zdem,nGreen,nRed,nMIR,rf,QL,rRed_darkcloud,...
    ndsi_pass1,ndsi_pass2,rRed_pass1,rRed_pass2,dz,fsnow_lim,...
    fsnow_total_lim,rRed_backtocloud)

%% Inputs
%
% * ZL2: L2A reflectances (NxMxB double array, where B is the number of band)
% * Zc: cloud mask (Zc>0 is cloud) (NxM array)
% * Zdem: digital elevation model (NxM array)
% * nGreen, nRed, nMIR: index of green, red, SWIR band in ZL2
% * rf: resampling factor for cloud reflectance
% * QL: quicklooks? (boolean)
% * ndsi_pass1,ndsi_pass2,rRed_pass1,rRed_pass2,rRed_backtocloud:
% parameters for reflectance-based tests (see <castest_CESneige.html the documnetation for castest_CESneige>)
% * dz: elevation band width
% * fsnow_lim: minimum snow fraction in an elevation band to define zs
% * fsnow_total_lim: minimum snow fraction in the whole image after pass1 to go to pass2

%% Outputs
%
% * snowtest: snow presence/absence (NxM boolean)
% * cloudtestfinal: cloud presence/absence (NxM boolean)
% * z_center: centers of the elevation bands (vector)
% * B1, B2: snow cover contours after pass 1 and pass 2 (cell)
% * fsnow: total snow fraction in the image after pass 1
% * zs: snow elevation for pass 2
% * fsnow_z: snow fraction in each band
% * N: number of clear pixels in each elevation band
% * z_edges: upper and lower limits of the elevation bands

%% Initial cloud mask processing
% The L2A cloud mask is too conservative and much useful information for
% snow cover mapping is lost.
%
% We allow the reclassification of some cloud pixels in snow
% or no-snow only if they have a rather low reflectance. We select only these
% "dark clouds" because the NDSI test is robust to the snow/cloud confusion
% in this case
%%
% Initial cloud mask (incl. cloud shadows)
cloudtestinit = Zc>0;
%%
% Get the cloud shadows
code_shad = bin2dec(fliplr('00000011'));
cloudshadow = bitand(Zc,code_shad)>0;
%%
% The "dark cloud" are found with a threshold rRed_darkcloud
% in the red band after bilinear resampling of the original image
% to match the MACCS algorithm philosophy but the benefit of this was not
% yet evaluated.

rRedcoarse = imresize(ZL2(:,:,nRed), 1/rf,'bilinear');

%%
% Then we oversample to the initial resolution using nearest neighbour to have
% the same image size.
rRedcoarse_oversampl = imresize(rRedcoarse,rf,'nearest');

%%
% clear rRedcoarse to free up memory
clear rRedcoarse

%%
% These pixels are removed from the intial cloud mask unless they were
% flagged as a cloud shadow. The snow detection will not be applied where
% cloudtesttmp is true.
cloudtesttmp = ...
    (cloudtestinit & rRedcoarse_oversampl>rRed_darkcloud) | cloudshadow;

%% Pass 1 : first snow test
%%
% The test is based on the Normalized Difference Snow Index (ndsi0) and the
% reflectance value in the red channel
ndsi0 = (ZL2(:,:,nGreen)-ZL2(:,:,nMIR))./(ZL2(:,:,nGreen)+ZL2(:,:,nMIR));
%%
% A pixel is marked as snow covered if NDSI is higher than ndsi_pass1 and
% if the red reflectance is higher than Red_pass1
snowtest = ~cloudtesttmp & ndsi0>ndsi_pass1 & ZL2(:,:,nRed)>rRed_pass1;

%%
% Now we can update the cloud mask
% Some pixels were originally marked as cloud but were not reclassified as
% snow after pass 1. These pixels are marked as cloud if they have a high
% reflectance ("back to black").
% Otherwise we keep them as "no-snow" ("stayin alive").

cloudtestpass1 = cloudtesttmp ...
    | (~snowtest & cloudtestinit & ZL2(:,:,nRed)>rRed_backtocloud);

%%
% For the quicklooks we compute the boundary of the snow cover after pass
% 1.
%
%%
% _Warning this uses much computer time._
if QL
    [B1, ~] = bwboundaries(snowtest); % requires Matlab Image Processing Toolbox
else
    B1 = [];
end

%%
% Initialize some output variables as empty array in case they is not reached 
% in pass 2
B2 = [];
zs = [];
N = [];
bin = [];

%% Pass 2 : second snow test
% Based on the DEM, the scene is discretized in elevation band of height dz.
% The elevation bands start from the minimal elevation
% found in the DEM resampled at the image resolution.
% The edges of elevation band are :

z_edges = double(min(Zdem(:)):dz:max(Zdem(:)));

% NB) the colon operator j:i:k is the same as [j,j+i,j+2i, ...,j+m*i],
% where m = fix((k-j)/i).
%%
% The number of bins is :
nbins = length(z_edges)-1;
%%
% The mean elevation of each band is computed for the graphics but not used
% by the algorithm
z_center = mean([z_edges(2:end);z_edges(1:end-1)]);
%%
% The lower edge of each bin is used to define zs
z_loweredges=z_edges(1:end-1);
%%
% We get the number of pixels (N) which are cloud-free (at this step) in each
% bin, and the index array (bin) to identify the elevation band corresponding
% to a pixel in the cloud-free portion of the image
if nbins>0
    [N,~,bin] = histcounts(Zdem(~cloudtestpass1),z_edges);
end
%%
% Compute the fraction of snow pixels in each elevation band
fsnow_z = zeros(nbins,1);
fcloud_z = zeros(nbins,1);
if ~isempty(bin)
    %%
    % We collect the snow pixels only in the cloud free areas
    
    M = snowtest(~cloudtestpass1(:)); % this also reshapes snowtest from a
    % 2D array to 1D array to match the bin index array dimension
    %%
    % Then we start to loop over the each elevation band
    for i = 1:nbins
        %%
        % We sum the snow pixels and divide by the number of cloud-free pixels
        if N(i)>0
            fsnow_z(i) = sum(M(bin==i))/N(i);
            fcloud_z(i) = sum(cloudtestpass1(bin==i))/N(i);
        else
            fsnow_z(i) = NaN;
            fcloud_z(i) = NaN;
        end
    end
    
    %%
    % We compute the total fraction of snow pixels in the image
    fsnow = nnz(snowtest)/numel(snowtest);
    
    %%
    % The pass 2 snow test is not performed if there is not enough snow
    % detected in pass 1.    
    if fsnow>fsnow_total_lim
        %%
        % We get zs, the minimum snow elevation above which we apply pass
        % 2.
        % zs is *two elevation bands* below the band at which fsnow > fsnow_lim
        izs = find(fsnow_z>fsnow_lim,1,'first');
        zs = z_loweredges(max(izs-2,1));
    end
end

%%
% if zs was found then we apply the second snow test :
% A pixel is marked as snow covered if NDSI is higher than ndsi_pass2 and
% if the red reflectance is higher than Red_pass1... and if it is above zs!
if ~isempty(zs)
    snowtest2 = ~cloudtesttmp ... % we use cloudtesttmp again 
        & ndsi0>ndsi_pass2 ...
        & Zdem>zs ...
        & ZL2(:,:,nRed)>rRed_pass2;
    %%
    % We add these snow pixels in the snow mask from pass 1
    snowtest = snowtest2 | snowtest;
    %%
    % For the quicklooks we compute the boundary of the snow cover after pass 2
    % _Warning this uses much computer time._
    if QL
        [B2, ~] = bwboundaries(snowtest);
    end
end

%%
%% Final update of the cloud mask
% Some pixels were originally marked as cloud but were not reclassified as
% snow after pass 1. These pixels are marked as cloud if they have a high
% reflectance ("back to black").
% Otherwise we keep them as "no-snow" ("stayin alive").
cloudtestfinal = cloudtesttmp ...
    | (~snowtest & cloudtestinit & ZL2(:,:,nRed)>rRed_backtocloud);
