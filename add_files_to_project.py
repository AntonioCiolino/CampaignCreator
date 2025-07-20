import sys
from pbxproj import XcodeProject

def add_files_to_project(project_path, file_paths):
    project = XcodeProject.load(project_path)
    group = project.get_or_create_group('CampaignCreatorApp')

    for file_path in file_paths:
        project.add_file(file_path, parent=group)

    project.save()

if __name__ == '__main__':
    project_path = sys.argv[1]
    file_paths = sys.argv[2:]
    add_files_to_project(project_path, file_paths)
