% this is the master script used for training the kaggle-winning seizure
% detection classifier on a blackfynn dataset
% inputs are BF username, password, dataset ID, file names of sz and interictal annotations, and sampling rate
% NOTE: as the BF platform is in flux, the tsid part is still changing. Right now there is only one dataset on BF
% and this system is configured to work with that one (R951). When other datasets are added, the pipeline will need adjustments

% EDIT: updated to work with the new blackfynn api
% Username/password are no longer needed,
% Instead it's assumed that the Blackfynn profile is already set up

function trainMaster(szfile, interictalfile, fs)
    fprintf('Pulling seizure segments from Blackfynn...\n')
    err = system(['python pullClips.py ictal ' szfile]);
    if err
        return
    else
        fprintf('done\n')
    end
    
    fprintf('Pulling interictal segments from Blackfynn...\n')
    err = system(['python pullClips.py interictal ' interictalfile]);
    if err
        return
    else
        fprintf('done\n')
    end
    
    fprintf('Clipping segments and organizing for algorithm training...\n')
    clipForAlgoPipeline(fs, 'Ripley')
    fprintf('done\n')
    
    fprintf('Training classifier (make sure train.py has correct target)...')
    err = system('python liveAlgo/train.py')
    if err
        return
    else
        fprintf('done\n')
    end
    fprintf('All done.\nTrained classifier ready for use.\n') 
end
