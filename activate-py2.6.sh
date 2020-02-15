# Source this file to activate Python 2.6 environment.

python2.6 --version || {
    echo "Error: Must activate python2.6 first"
    return 1
}

export PYTHONUSERBASE=$PWD/.pyuser/py2.6
PATH=$PYTHONUSERBASE/bin:$PATH

alias python='python2.6'
alias pip='pip2.6'
alias pipi='pip2.6 install --user'

cat << EOF
Aliases:
    python = python2.6
    pip = pip2.6
    pipi = pip install --user

Prepare for testing:
    pipi -e .
    pipi pytest
    pytest
EOF
