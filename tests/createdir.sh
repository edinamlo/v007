#!/usr/bin/env bash
set -e
mkdir -p sample_media/Movies/"Inception (2010)"
mkdir -p sample_media/Movies/"Matrix (1999)"
mkdir -p sample_media/Movies/"1917 (2019)"
mkdir -p "sample_media/TV/9-1-1 - Lone Star (2020) S01-S02"
mkdir -p "sample_media/TV/The Mandalorian S01"
mkdir -p "sample_media/Anime/Naruto Shippuden"
mkdir -p "sample_media/Anime/One Piece"

touch "sample_media/Movies/Inception (2010)/Inception.2010.1080p.BluRay.x264.YIFY.mkv"
touch "sample_media/Movies/Matrix (1999)/Matrix.1999.720p.HDTV.x265.NF.mp4"
touch "sample_media/Movies/1917 (2019)/1917 BluRay 1080pxH264 Ita Eng AC3 5.1 Sub Ita Eng.mkv"
touch "sample_media/TV/9-1-1 - Lone Star (2020) S01-S02/README.txt"
touch "sample_media/TV/The Mandalorian S01/Chapter1.mkv"
touch "sample_media/Anime/Naruto Shippuden/Naruto.Shippuden.(001-500).mkv"
touch "sample_media/Anime/One Piece/One.Piece.S01E1116.Lets.Go.Get.It!.2160p.mkv"
echo "Sample media created."
