param(
    [string]$Message = "Update"
)

# Stage all changes
git add .

# Commit with the provided message
git commit -m $Message

# Push to the remote repository
git push
