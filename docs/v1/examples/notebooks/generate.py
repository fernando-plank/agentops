import os
import subprocess

# Before generating, `brew install pandoc`


import os
import subprocess


def convert_notebooks_to_html(source_dir: str, target_dir: str):
    # Ensure the target directory exists
    os.makedirs(target_dir, exist_ok=True)

    # Loop over all files in the source directory and subdirectories
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            # Check if current file has a .ipynb extension
            if filename.endswith(".ipynb"):
                # Construct full file path
                source_file = os.path.join(root, filename)
                # Create a mirrored directory structure in the target directory
                relative_dir = os.path.relpath(root, source_dir)
                html_target_dir = os.path.join(target_dir, relative_dir)
                os.makedirs(html_target_dir, exist_ok=True)
                # Construct target file path
                html_target_file = os.path.join(
                    html_target_dir, filename[:-6] + ".html"
                )  # remove '.ipynb' and add '.html'

                # Convert notebook to HTML using pandoc
                # -c https://app.agentops.ai/notebook_styles.css to add custom styles
                subprocess.check_call(
                    "pandoc {source_file} -s -o {html_target_file} -c https://app.agentops.ai/notebook_styles.css && "
                    "{{ echo '<!-- This file was generated by Pandoc -->'; cat {html_target_file}; }} > temp.md && mv temp.md {html_target_file}".format(
                        source_file=source_file, html_target_file=html_target_file
                    ),
                    shell=True,
                )


# Example usage:
try:
    convert_notebooks_to_html("../../../../examples", "./")
except FileNotFoundError:
    try:
        convert_notebooks_to_html("docs/v1/examples", "./")
    except FileNotFoundError:
        print(
            "Could not find notebooks folder. Run this script from project root or at the script location."
        )
