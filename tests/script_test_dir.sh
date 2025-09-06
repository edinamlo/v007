#!/bin/bash

# create_sample_media.sh - Replicate exact structure from PTT tests with matching dir/file names

set -e

# Create base directory
mkdir -p sample_media

echo "Creating media structure based on PTT tests examples..."

# Function to create directory and file with same name
create_media() {
    local dir_name="$1"
    local file_name="$2"
    mkdir -p "sample_media/$dir_name"
    touch "sample_media/$dir_name/$file_name"
}

# Movie examples
create_media "Inception.2010.1080p.BluRay.x264.YIFY" "Inception.2010.1080p.BluRay.x264.YIFY.mkv"
create_media "Inception.2010.1080p.BluRay.x264.YIFY" "Inception.2010.1080p.BluRay.x264.YIFY.srt"
create_media "Inception.2010.1080p.BluRay.x264.YIFY" "Inception.2010.1080p.BluRay.x264.YIFY.nfo"

create_media "The.Dark.Knight.2008.720p.BluRay.x264-RARBG" "The.Dark.Knight.2008.720p.BluRay.x264-RARBG.mkv"
create_media "The.Dark.Knight.2008.720p.BluRay.x264-RARBG" "The.Dark.Knight.2008.720p.BluRay.x264-RARBG.srt"

create_media "Pulp.Fiction.1994.1080p.BluRay.x264-DIMENSION" "Pulp.Fiction.1994.1080p.BluRay.x264-DIMENSION.mkv"

create_media "The.Matrix.1999.4K.BluRay.x265.10bit-HDR.5.1-PSYPHER" "The.Matrix.1999.4K.BluRay.x265.10bit-HDR.5.1-PSYPHER.mkv"
create_media "The.Matrix.1999.4K.BluRay.x265.10bit-HDR.5.1-PSYPHER" "The.Matrix.1999.4K.BluRay.x265.10bit-HDR.5.1-PSYPHER.srt"

# TV Show examples - each episode gets its own directory
create_media "Breaking.Bad.S01E01.720p.BluRay.x264-DIMENSION" "Breaking.Bad.S01E01.720p.BluRay.x264-DIMENSION.mkv"
create_media "Breaking.Bad.S01E01.720p.BluRay.x264-DIMENSION" "Breaking.Bad.S01E01.720p.BluRay.x264-DIMENSION.srt"

create_media "Breaking.Bad.S01E02.720p.BluRay.x264-DIMENSION" "Breaking.Bad.S01E02.720p.BluRay.x264-DIMENSION.mkv"

create_media "Breaking.Bad.S01E03.720p.BluRay.x264-DIMENSION" "Breaking.Bad.S01E03.720p.BluRay.x264-DIMENSION.mkv"

create_media "Breaking.Bad.S02E01.720p.BluRay.x264-DIMENSION" "Breaking.Bad.S02E01.720p.BluRay.x264-DIMENSION.mkv"

create_media "Breaking.Bad.S02E02.720p.BluRay.x264-DIMENSION" "Breaking.Bad.S02E02.720p.BluRay.x264-DIMENSION.mkv"

create_media "Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD" "Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD.mkv"
create_media "Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD" "Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD.srt"

create_media "Game.of.Thrones.S01E02.1080p.BluRay.x264-REWARD" "Game.of.Thrones.S01E02.1080p.BluRay.x264-REWARD.mkv"

create_media "Game.of.Thrones.S08E01.2160p.WEB-DL.x265.10bit.HDR.DTS-HD.MA.TrueHD.7.1.Atmos-SWTYBLZ" "Game.of.Thrones.S08E01.2160p.WEB-DL.x265.10bit.HDR.DTS-HD.MA.TrueHD.7.1.Atmos-SWTYBLZ.mkv"

create_media "Game.of.Thrones.S08E02.2160p.WEB-DL.x265.10bit.HDR.DTS-HD.MA.TrueHD.7.1.Atmos-SWTYBLZ" "Game.of.Thrones.S08E02.2160p.WEB-DL.x265.10bit.HDR.DTS-HD.MA.TrueHD.7.1.Atmos-SWTYBLZ.mkv"

# Anime examples
create_media "Naruto.S01E01.720p.WEB-DL.x264-ERAI" "Naruto.S01E01.720p.WEB-DL.x264-ERAI.mkv"
create_media "Naruto.S01E01.720p.WEB-DL.x264-ERAI" "Naruto.S01E01.720p.WEB-DL.x264-ERAI.ass"

create_media "Naruto.S01E02.720p.WEB-DL.x264-ERAI" "Naruto.S01E02.720p.WEB-DL.x264-ERAI.mkv"

create_media "Naruto.S01E03.720p.WEB-DL.x264-ERAI" "Naruto.S01E03.720p.WEB-DL.x264-ERAI.mkv"

create_media "One.Piece.S01E01.1080p.WEB-DL.x265.10bit-SUBSPLEASE" "One.Piece.S01E01.1080p.WEB-DL.x265.10bit-SUBSPLEASE.mkv"
create_media "One.Piece.S01E01.1080p.WEB-DL.x265.10bit-SUBSPLEASE" "One.Piece.S01E01.1080p.WEB-DL.x265.10bit-SUBSPLEASE.ass"

create_media "One.Piece.S01E02.1080p.WEB-DL.x265.10bit-SUBSPLEASE" "One.Piece.S01E02.1080p.WEB-DL.x265.10bit-SUBSPLEASE.mkv"

create_media "Attack.on.Titan.S01E01.1080p.BluRay.x264-HORRIBLESUBS" "Attack.on.Titan.S01E01.1080p.BluRay.x264-HORRIBLESUBS.mkv"
create_media "Attack.on.Titan.S01E01.1080p.BluRay.x264-HORRIBLESUBS" "Attack.on.Titan.S01E01.1080p.BluRay.x264-HORRIBLESUBS.ass"

# Additional examples
create_media "Stranger.Things.S01E01.1080p.NF.WEB-DL.DDP5.1.x264-NTb" "Stranger.Things.S01E01.1080p.NF.WEB-DL.DDP5.1.x264-NTb.mkv"

create_media "Stranger.Things.S01E02.1080p.NF.WEB-DL.DDP5.1.x264-NTb" "Stranger.Things.S01E02.1080p.NF.WEB-DL.DDP5.1.x264-NTb.mkv"

create_media "The.Office.US.S01E01.720p.WEB-DL.x264-AMZN" "The.Office.US.S01E01.720p.WEB-DL.x264-AMZN.mkv"

create_media "The.Office.US.S01E02.720p.WEB-DL.x264-AMZN" "The.Office.US.S01E02.720p.WEB-DL.x264-AMZN.mkv"

create_media "The.Mandalorian.S01E01.2160p.DSNP.WEB-DL.DDP5.1.HDR.HEVC-CMRG" "The.Mandalorian.S01E01.2160p.DSNP.WEB-DL.DDP5.1.HDR.HEVC-CMRG.mkv"

create_media "The.Mandalorian.S01E02.2160p.DSNP.WEB-DL.DDP5.1.HDR.HEVC-CMRG" "The.Mandalorian.S01E02.2160p.DSNP.WEB-DL.DDP5.1.HDR.HEVC-CMRG.mkv"

# More complex examples
create_media "Interstellar.2014.IMAX.1080p.BluRay.x264.DTS-HD.MA.5.1-FGT" "Interstellar.2014.IMAX.1080p.BluRay.x264.DTS-HD.MA.5.1-FGT.mkv"
create_media "Interstellar.2014.IMAX.1080p.BluRay.x264.DTS-HD.MA.5.1-FGT" "Interstellar.2014.IMAX.1080p.BluRay.x264.DTS-HD.MA.5.1-FGT.srt"

create_media "Blade.Runner.2049.2017.2160p.BluRay.x265.10bit.HDR.TrueHD.7.1.Atmos-SWTYBLZ" "Blade.Runner.2049.2017.2160p.BluRay.x265.10bit.HDR.TrueHD.7.1.Atmos-SWTYBLZ.mkv"

# Avatar examples with different quality levels
create_media "Avatar.2009.1080p.BluRay.x264.DTS-HD.MA.5.1-FGT" "Avatar.2009.1080p.BluRay.x264.DTS-HD.MA.5.1-FGT.mkv"

create_media "Avatar.2009.720p.BluRay.x264.DTS-HD.MA.5.1-FGT" "Avatar.2009.720p.BluRay.x264.DTS-HD.MA.5.1-FGT.mkv"

create_media "Avatar.2009.480p.DVDrip.x264-ETRG" "Avatar.2009.480p.DVDrip.x264-ETRG.mkv"

# Extended edition example
create_media "The.Lord.of.the.Rings.The.Fellowship.of.the.Ring.2001.EXTENDED.1080p.BluRay.x264.DTS.5.1-HDMaN" "The.Lord.of.the.Rings.The.Fellowship.of.the.Ring.2001.EXTENDED.1080p.BluRay.x264.DTS.5.1-HDMaN.mkv"

# HDR example
create_media "Dune.2021.2160p.UHD.BluRay.x265.10bit.HDR.DTS-HD.MA.5.1-SWTYBLZ" "Dune.2021.2160p.UHD.BluRay.x265.10bit.HDR.DTS-HD.MA.5.1-SWTYBLZ.mkv"

# WEB examples
create_media "The.Witcher.S01E01.1080p.NF.WEB-DL.DDP5.1.H.264-NTb" "The.Witcher.S01E01.1080p.NF.WEB-DL.DDP5.1.H.264-NTb.mkv"

create_media "The.Witcher.S01E02.1080p.NF.WEB-DL.DDP5.1.H.264-NTb" "The.Witcher.S01E02.1080p.NF.WEB-DL.DDP5.1.H.264-NTb.mkv"

# Create some metadata files
touch "sample_media/RARBG.txt"
touch "sample_media/RARBG_DO_NOT_MIRROR.exe"
touch "sample_media/YIFY.txt"
touch "sample_media/Sample.mkv"

# Create some additional subtitle files
create_media "Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD.eng" "Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD.eng.srt"
create_media "Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD.spa" "Game.of.Thrones.S01E01.1080p.BluRay.x264-REWARD.spa.srt"

# Create some sample directories with mixed content
create_media "Some.Movie.2020.1080p.WEB-DL.x264-ASDF" "Some.Movie.2020.1080p.WEB-DL.x264-ASDF.mkv"
create_media "Another.Movie.2019.720p.BluRay.x264-QWER" "Another.Movie.2019.720p.BluRay.x264-QWER.mkv"

# Create some torrent files (each in their own directory)
create_media "Inception.2010.1080p.BluRay.x264.YIFY.torrent" "Inception.2010.1080p.BluRay.x264.YIFY.torrent"
create_media "Breaking.Bad.S01.720p.BluRay.x264-DIMENSION.torrent" "Breaking.Bad.S01.720p.BluRay.x264-DIMENSION.torrent"
create_media "Game.of.Thrones.S08.2160p.WEB-DL.x265.10bit.HDR.DTS-HD.MA.TrueHD.7.1.Atmos-SWTYBLZ.torrent" "Game.of.Thrones.S08.2160p.WEB-DL.x265.10bit.HDR.DTS-HD.MA.TrueHD.7.1.Atmos-SWTYBLZ.torrent"

echo "Sample media structure created based on PTT tests examples!"
echo "Total directories: $(find sample_media -type d | wc -l)"
echo "Total files: $(find sample_media -type f | wc -l)"
echo ""
echo "Structure created:"
find sample_media -type f | head -20
echo "..."
echo ""
echo "Run 'tree sample_media/' to see the full directory structure"