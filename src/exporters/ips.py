import tarfile, os

class export_ips:
    """Class used to save a session"""
    
    def __init__(self, sessiondir):
        """Initialize with session directory to save"""
        self.sessiondir = sessiondir
    
    def export(self, outputdir):
        """Save session directory to outputdir file"""
        
        # Add .ips as the extention if left off
        if outputdir[-4:] != '.ips':
            outputdir += '.ips'
        
        # Package the session directory as a .tar.bz2 file
        tar = tarfile.open(outputdir,'w:bz2')
        tar.add(self.sessiondir, os.path.basename(self.sessiondir))
        tar.close()