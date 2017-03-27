% this is the master script used for training the kaggle-winning seizure
% detection classifier on a blackfynn dataset

function trainMaster(username, passwd, tsid, ptname, szfile, interictalfile, fs)
   fprintf('Pulling seizure clips from Blackfynn...')
   system(['python pullSzClips.py ' username ' ' passwd ' ' tsid ' ' ptname ' ' szfile])
   fprtinf('done\n')
   fprintf('Pulling interictal segments from Blackfynn...')
   system(['python pullInterictalClips.py ' username ' ' passwd ' ' tsid ' ' ptname ' ' interictalfile])
   fprintf('done\n')
   fprintf('Clipping segments and organizing for algorithm training...')
   clipForAlgoPipeline(fs,ptname)
   fprintf('done\n')
   fprintf('Training classifier (make sure train.py has correct target)...')
   system('python liveAlgo/train.py')
   fprintf('All done.\nTrained classifier ready for use.\n') 
end