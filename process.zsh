#!/bin/zsh
# One-time preprocessing script for Klar
# Run on macOS host: zsh process.zsh

set -e

echo "🔧 Klar - Preprocessing Assets"
echo "=============================="

# Ensure we're in project root
cd "$(dirname "$0")"

# Create directories
mkdir -p frontend/01/assets

# --- 1. Generate PNG icons from SVG ---
echo "\n📦 Generating icons from logo.svg..."

# Check for rsvg-convert (from librsvg)
if ! command -v rsvg-convert &> /dev/null; then
    echo "Installing librsvg via Homebrew..."
    brew install librsvg
fi

# Generate PWA icons
rsvg-convert -w 16 -h 16 assets/logo.svg -o frontend/01/assets/favicon-16.png
rsvg-convert -w 32 -h 32 assets/logo.svg -o frontend/01/assets/favicon-32.png
rsvg-convert -w 180 -h 180 assets/logo.svg -o frontend/01/assets/apple-touch-icon.png
rsvg-convert -w 192 -h 192 assets/logo.svg -o frontend/01/assets/icon-192.png
rsvg-convert -w 512 -h 512 assets/logo.svg -o frontend/01/assets/icon-512.png

# Generate favicon.ico (multi-size)
if command -v convert &> /dev/null; then
    convert frontend/01/assets/favicon-16.png frontend/01/assets/favicon-32.png frontend/01/assets/favicon.ico
    echo "✅ favicon.ico created"
else
    echo "⚠️  ImageMagick not found. Install with: brew install imagemagick"
    echo "   For now, using 32px PNG as favicon"
    cp frontend/01/assets/favicon-32.png frontend/01/assets/favicon.ico
fi

# Copy SVG for use in app
cp assets/logo.svg frontend/01/assets/logo.svg

echo "✅ Icons generated"

# --- 2. Create symlink for data.csv ---
echo "\n🔗 Creating symlinks..."

cd frontend/01
ln -sf ../../data.csv data.csv
cd ../..

echo "✅ data.csv symlinked"

# --- 3. Generate manifest.json ---
echo "\n📱 Creating PWA manifest..."

cat > frontend/01/manifest.json << 'MANIFEST'
{
  "name": "Klar - Capital, Clarified",
  "short_name": "Klar",
  "description": "Investor CRM for Silversky Capital",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#15213B",
  "theme_color": "#15213B",
  "orientation": "any",
  "icons": [
    {
      "src": "/assets/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/assets/apple-touch-icon.png",
      "sizes": "180x180",
      "type": "image/png"
    }
  ],
  "categories": ["business", "finance", "productivity"]
}
MANIFEST

echo "✅ manifest.json created"

# --- 4. Verify cities.json exists ---
if [ -f "frontend/01/assets/cities.json" ]; then
    echo "\n✅ cities.json already exists"
else
    echo "\n⚠️  cities.json not found - will be created by build"
fi

# --- Summary ---
echo "\n=============================="
echo "✅ Preprocessing complete!"
echo ""
echo "Generated files:"
ls -la frontend/01/assets/
echo ""
echo "Symlinks:"
ls -la frontend/01/data.csv

echo "\nReady to build Phase 1!"
