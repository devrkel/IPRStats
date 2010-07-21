from setuptools import setup, find_packages
import glob
import os
import sys

OPTIONS={}
SCRIPTS=[]
SETUP_REQUIRES=[]

if sys.argv[1] == 'py2app':
    import py2app
    OPTIONS['py2app'] = {'packages':['wx'], 'site_packages':True,
                         'argv_emulation':True, 'iconfile':'IPRStats.icns'}
    SETUP_REQUIRES.append('py2app')
elif sys.argv[1] == 'bdist_wininst':
    SCRIPTS.append(os.path.join('scripts','iprstats_postinstall.py'))
    SCRIPTS.append(os.path.join('scripts','iprs.pyw'))

setup(name='IPRStats',
      app=['iprstats/iprstats.py'],
      version='0.4',
      description='A statistical tool that eases the analysis of ' + \
                  'InterProScan results by generating charts and tables ' + \
                  'with links to additional information.',
      author='Ryan Kelly',
      author_email='kellyrj2@muohio.edu',
      url='http://github.com/devrkel/IPRStats',
      packages=find_packages(),
      data_files=[("data",
                   glob.glob(os.path.join('iprstats', 'data', '*.*'))
                   )],
      install_requires=["wxPython"],
      setup_requires=SETUP_REQUIRES,
      options=OPTIONS,
      scripts=SCRIPTS
)
