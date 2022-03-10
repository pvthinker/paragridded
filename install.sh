#!/bin/bash

paragdir=$HOME/.paragridded
default=defaults.yaml
srcdir=`pwd`

echo "--------------------------------------------------------------------------------"
echo ""
echo " Installing paragridded"
echo ""
if [ ! -d "$paragdir" ]; then
    echo "  Create $paragdir"
    mkdir $paragdir
fi
if [ ! -f "$paragdir/$default" ]; then
    echo "  Copy $default in $pydir"
    echo "  Set the paragridded src to $srcdir" 
    sed "s|DIRECTORY_TO_PARAGRIDDED|${srcdir}|" $default > $paragdir/$default
fi

# for bash users
cat > $paragdir/activate.sh << EOF
export PYTHONPATH=\$PYTHONPATH:`pwd`/core:`pwd`/diags
echo Python now knows that paragridded is in `pwd`
EOF

# for csh, tcsh users
cat > $paragdir/activate.csh << EOF
setenv PYTHONPATH \$PYTHONPATH:`pwd`/core:`pwd`/diags
echo Python now knows that paragridded is in `pwd`
EOF

# copy the experiment into

echo ""
echo "  To complete the installation you need to edit"
echo ""
echo "      $paragdir/$default"
echo ""
echo "  and set the various directories"
echo ""
echo "  Once this is okay you're good to go"
echo ""
echo "  Each time you open a new terminal you need to"
echo "     source ~/.paragridded/activate.sh  if you're under bash"
echo "  or source ~/.paragridded/activate.csh  if you're under csh/tcsh"
echo ""

