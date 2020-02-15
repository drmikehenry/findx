# Source this file to activate Python 3.3 environment.

python3.3 --version || {
    echo "Error: Must activate python3.3 first"
    return 1
}

export PYTHONUSERBASE=$PWD/.pyuser/py3.3
PATH=$PYTHONUSERBASE/bin:$PATH

alias python='python3.3'
alias pip='pip3.3'
alias pipi='pip3.3 install --user'

cat << EOF
Aliases:
    python = python3.3
    pip = pip3.3
    pipi = pip install --user (**NOTE** 'pipi -e .' fails!)

Prepare for testing:
    python setup.py develop --user
    pipi pytest
    pytest
EOF
