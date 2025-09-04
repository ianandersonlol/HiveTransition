[View Script: broken.py](../../broken.py)

# Broken Script Reporter

## Overview
The `broken.py` script helps users report issues with scripts that aren't working after migration. It generates a pre-filled GitHub issue URL containing the script content, making bug reporting quick and standardized.

## What It Does

1. **Reads the problematic script**
2. **Generates a GitHub issue URL** with:
   - Pre-filled title: `[BUG] Script issue: {filename}`
   - Script content in a code block
   - Script's absolute path
   - Auto-assignment to `ianandersonlol`
   - Bug label applied
3. **Provides the URL** for users to copy and paste

## Usage

### Basic Usage
```bash
python broken.py <script_filename>
```

### Example
```bash
python broken.py my_failing_job.sh
```

### Output
```
GitHub issue URL generated successfully!

Copy and paste this URL into your browser:
--------------------------------------------------------------------------------
https://github.com/ianandersonlol/HiveTransition/issues/new?title=%5BBUG%5D...
--------------------------------------------------------------------------------

Note: The URL might be very long due to the script content.
```

## What Gets Included

### Issue Title
- Format: `[BUG] Script issue: {script_name}`
- Example: `[BUG] Script issue: colabfold_job.sh`

### Issue Body
The generated issue includes:

1. **Script Section**
   - Full script content in a bash code block
   - Syntax highlighted for readability

2. **Description Section**
   - Placeholder for user to describe the problem
   - Prompts for what happened vs. expected behavior

3. **Metadata**
   - Full script path
   - Note that it was submitted using `broken.py`

### Example Issue Content
The generated GitHub issue will look like this:

**Title:** `[BUG] Script issue: my_failing_job.sh`

**Body:**
```
## Script
#!/bin/bash
#SBATCH --job-name=test
... (full script content) ...

## What happened? What should have happened?
<!-- Describe what went wrong and what you expected to happen -->

---
Script path: /home/user/scripts/my_failing_job.sh
Submitted using: broken.py
```

## When to Use This Tool

### Good Candidates for Bug Reports

1. **Migration tool didn't fix something**
   - Path not updated correctly
   - Missing SLURM flags
   - Incorrect partition assignment

2. **Script fails on HIVE**
   - Worked on old cluster
   - Module not found errors
   - Permission issues

3. **Unexpected behavior**
   - Different output than before
   - Performance issues
   - Resource allocation problems

### Before Reporting

1. **Try the appropriate fix script first:**
   - `colab_fix.py` for ColabFold
   - `ligandmpnn_fix.py` for LigandMPNN
   - `rfdiffusion_fix.py` for RFdiffusion
   - `rosetta_fix.py` for Rosetta

2. **Check common issues:**
   - Paths exist on HIVE
   - Modules are available
   - Permissions are correct

3. **Verify the basics:**
   - Can you SSH to HIVE?
   - Does the software exist?
   - Are your files transferred?

## URL Length Limitations

If you get an error about URL being too long:

1. **Manual submission:**
   ```
   1. Go to: https://github.com/ianandersonlol/HiveTransition/issues/new
   2. Manually fill in the issue with the script content
   ```

2. **Reduce script size:**
   - Remove comments
   - Remove redundant sections
   - Focus on the problematic part

3. **Use file attachment:**
   - Create issue with summary
   - Attach full script as file

## Information to Add

When using the generated URL, please add:

1. **Error messages**
   ```
   Paste any error output here
   ```

2. **Expected behavior**
   - What should happen
   - What worked before

3. **Environment details**
   - Which migration tool you used
   - When the script last worked
   - Any modifications you made

4. **Steps to reproduce**
   - Exact commands run
   - Order of operations
   - Any dependencies

## Privacy Considerations

The script includes your full script content, which might contain:
- Project paths
- Usernames
- Research details

Review before submitting and redact sensitive information if needed.

## Troubleshooting

### File Not Found
```
Error: File 'script.sh' not found.
```
- Check file path and name
- Use absolute or relative path

### URL Generation Failed
- Check for special characters in script
- Ensure file is readable
- Try with a smaller test script

### Can't Access GitHub
- Check internet connection
- Verify GitHub access
- Try direct issue creation

## Alternative Reporting Methods

If `broken.py` doesn't work for your case:

1. **Direct GitHub Issue**
   - Go to: https://github.com/ianandersonlol/HiveTransition/issues/new
   - Use the template
   - Attach script file

2. **Email Report**
   - Send to designated admin
   - Include script and error details

3. **Slack/Teams Channel**
   - Post in migration support channel
   - Include relevant details

## Best Practices

1. **One issue per script type**
   - Group similar problems
   - Reference related issues

2. **Clear descriptions**
   - Specific error messages
   - Exact commands used
   - Timeline of events

3. **Follow up**
   - Respond to questions
   - Test proposed fixes
   - Confirm resolution

## Important Notes

1. **Public Repository**: Issues are visible to everyone
2. **Auto-Assignment**: Goes directly to `ianandersonlol`
3. **Response Time**: Varies based on complexity
4. **Collaborative Fixes**: Others may contribute solutions

## Related Documentation
- See individual script docs for specific issues
- Check README.md for general migration info
- Review GitHub issue history for similar problems