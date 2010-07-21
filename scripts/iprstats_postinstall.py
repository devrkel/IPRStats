import os
import sys

try:
    try:
        cutsfldr = get_special_folder_path("CSIDL_COMMON_STARTMENU")
    except:
        cutsfldr = get_special_folder_path("CSIDL_STARTMENU")
    if os.path.isdir(cutsfldr):
        shortcut = os.path.join(cutsfldr, "IPRStats.lnk")
        create_shortcut(os.path.join(sys.prefix, 'scripts', 'iprs.pyw'),
                        'IPRStats', shortcut)
        file_created(shortcut)
    else:
        pass
except Exception, details:
    print details
