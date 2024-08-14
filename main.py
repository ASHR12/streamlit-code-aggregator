import streamlit as st
from github import Github
import requests
import os
import config

# Function to fetch repository contents recursively
def get_repo_contents(repo_url, branch, exclude_extensions, exclude_filenames):
    # Extract owner and repo name from URL
    parts = repo_url.split('/')
    owner = parts[-2]
    repo_name = parts[-1]
    
    g = Github()  # This uses GitHub's default rate limit. For more requests, consider using a token.
    repo = g.get_repo(f"{owner}/{repo_name}")
    
    try:
        contents = repo.get_contents("", ref=branch)
    except Exception as e:
        st.error(f"Failed to access the repository or branch: {e}")
        return []

    processed_files = []
    def process_contents(contents, path=""):
        for content_file in contents:
            full_path = os.path.join(path, content_file.name)
            if content_file.type == "dir":
                # Recursively process directories
                sub_contents = repo.get_contents(content_file.path, ref=branch)
                process_contents(sub_contents, full_path)
            elif content_file.type == "file":
                # Check if the file should be excluded based on extension or name
                if not any(content_file.path.endswith(ext) for ext in exclude_extensions) and \
                   not any(content_file.name == name for name in exclude_filenames):
                    processed_files.append(content_file)
                    st.write(f"Processing: {full_path}")

    process_contents(contents)
    return processed_files

# Function to download and concatenate file contents with paths
def concatenate_files(contents):
    full_text = ""
    for file in contents:
        if file.download_url:
            try:
                response = requests.get(file.download_url)
                if response.status_code == 200:
                    # Add file path before content
                    full_text += f"### {file.path}\n\n"
                    full_text += response.text + "\n\n"
            except requests.RequestException as e:
                st.error(f"Failed to download {file.path}: {e}")
    return full_text

# Streamlit UI
st.title("GitHub Repository Text Consolidator")

# Input for GitHub repository URL
repo_url = st.text_input("Enter the GitHub repository URL:")

# Input for branch
branch = st.text_input("Enter the branch name:")

# Display excluded extensions from config
st.write(f"Excluded file extensions: {', '.join(config.EXCLUDE_EXTENSIONS)}")

# Display excluded file from config
st.write(f"Excluded file : {', '.join(config.EXCLUDE_FILENAMES)}")

if st.button("Process Repository"):
    if repo_url and branch:
        try:
            contents = get_repo_contents(repo_url, branch, config.EXCLUDE_EXTENSIONS, config.EXCLUDE_FILENAMES)
            if contents:
                text = concatenate_files(contents)
                
                # Create a temporary file to store the concatenated text
                temp_file = "consolidated_text.txt"
                # Open the file with UTF-8 encoding
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(text)
                
                # Provide download link
                st.success("Text files have been consolidated!")
                with open(temp_file, "rb") as file:
                    btn = st.download_button(
                        label="Download Consolidated Text",
                        data=file,
                        file_name=temp_file,
                        mime="text/plain"
                    )
                # Remove temporary file
                os.remove(temp_file)
        except Exception as e:
            st.error(f"An error occurred during processing: {e}")
    else:
        st.warning("Please enter both a GitHub repository URL and a branch name.")

st.info("This application only works with public GitHub repositories.")