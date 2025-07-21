import sys
from pbxproj import XcodeProject

def fix_project_paths(project_path, file_names):
    project = XcodeProject.load(project_path)

    for file_name in file_names:
        file_refs = project.get_files_by_name(file_name)
        for file_ref in file_refs:
            file_ref.path = file_name

    project.save()

if __name__ == '__main__':
    project_path = sys.argv[1]
    file_names = sys.argv[2:]
    fix_project_paths(project_path, file_names)
