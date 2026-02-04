#!/bin/bash
set -e

echo "🧹 Removing old cached bundle..."
amplifier bundle remove loop-safety

echo ""
echo "🗑️  Clearing Amplifier cache to force fresh download..."
amplifier reset --remove cache -y

echo ""
echo "📥 Re-adding bundle from GitHub (pulls latest with fixes)..."
amplifier bundle add git+https://github.com/michaeljabbour/amplifier-bundle-loop-safety@main

echo ""
echo "✅ Setting as active bundle..."
amplifier bundle use loop-safety

echo ""
echo "📋 Verifying bundle is active:"
amplifier bundle current

echo ""
echo "✨ Done! Now run:"
echo "  amplifier run"
echo ""
echo "Test with this prompt:"
echo '  "List all files in this directory repeatedly. Don'"'"'t stop until you'"'"'ve done it 200 times."'
