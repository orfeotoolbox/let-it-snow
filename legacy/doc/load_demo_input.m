function [satlist,sitelist,datelist]=load_demo_input(list)
%[satlist,sitelist,datelist]=load_demo_input(list)
% Load the names of the sensor, site and date to process a batch of images
% list: 'all' (only option so far)

switch list
    case 'all'
        
        satlist={'Take5','Landsat8'};
        sitelist{1}={'Sudmipy-O','Sudmipy-E','Alpes','Maroc'};
        sitelist{2}={'D0005H0001','D0005H0002'};
        
        for isat=1:length(satlist)
            sat=satlist{isat};
            nsite=length(sitelist{isat});
            for isite=1:nsite
                site=sitelist{isat}{isite};
                pL2=['../' sat '/AOI_test_CESNeige/LEVEL2A/' site];
                fL2=dir([pL2 '/*PENTE*.TIF']);
                ndate=length(fL2);
                for idate=1:ndate
                    index=strfind(fL2(idate).name,'_20');
                    datelist{isat}{isite}{idate}=fL2(idate).name(index+1:index+8);
                end
            end
        end
    otherwise
        error('incorrect argument')
end
