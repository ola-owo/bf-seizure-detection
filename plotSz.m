function plotSz(varargin)
    num_seizures = varargin{1};
    if nargin == 2
        num_channels = varargin{2};
    else
        num_channels = 4;
    end

    for sz_no = 1:num_seizures
        load(sprintf('sz%d.mat', sz_no), 'clip');
        figure;
        suptitle(sprintf('Seizure %d', sz_no));
        for ch = 1:num_channels
            subplot(4,1,ch);
            plot(clip(:,ch));
        end
    end
end