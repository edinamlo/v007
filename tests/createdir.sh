#!/usr/bin/env bash
# Create folders in /workspaces/v007/sample_media and put a sample file inside each
set -euo pipefail

BASE="/workspaces/v007/sample_media"
mkdir -p "$BASE"
cd "$BASE"

names=(
"Sword.Art.Online.Alternative.S01.v2.1080p.Blu-Ray.10-Bit.Dual-Audio.LPCM.x265-iAHD"
"[SubsPlease] Tearmoon Teikoku Monogatari - 01 (1080p) [15ADAE00].mkv"
"[SubsPlease] Fairy Tail - 100 Years Quest - 05 (1080p) [1107F3A9].mkv"
"[Erai-raws] Tearmoon Teikoku Monogatari - 01 [1080p][Multiple Subtitle] [ENG][POR-BR][SPA-LA][SPA][ARA][FRE][GER][ITA][RUS]"
"Hunter x Hunter (2011) - 01 [1080p][Multiple Subtitle] [ENG][POR-BR][SPA-LA][SPA][ARA][FRE][GER][ITA][RUS]"
"Naruto Shippuden (001-500) [Complete Series + Movies] (Dual Audio)"
"[Erai-raws] Sword Art Online Alternative - Gun Gale Online - 10 [720p][Multiple Subtitle].mkv"
"One.Piece.S01E1116.Lets.Go.Get.It!.Buggys.Big.Declaration.2160p.B-Global.WEB-DL.JPN.AAC2.0.H.264.MSubs-ToonsHub.mkv"
"[Erai-raws] 2-5 Jigen no Ririsa - 08 [480p][Multiple Subtitle][972D0669].mkv"
"[Exiled-Destiny]_Tokyo_Underground_Ep02v2_(41858470).mkv"
)

for name in "${names[@]}"; do
  mkdir -p -- "$name"
  # create a sample file inside each folder with the exact same base name
  touch -- "$name/$name.sample"
done