# Showzstore follow-up review (2026-09-30, base origin/main d1be5b78)

Dry run by default: `python3 scripts/showz-followup-fixes.py` (`--apply` writes oneshot.json, figure-sku-aliases.json and showz-followup-stats.json).
Dry run: 29,430 → 29,361 rows (−69 = 39 merges + 8 stub merges + 22 invented deletions); 16 field fixes; no new dangling aliases or setIds; no duplicate ids.

| bucket | merge | mergeStub | fixName | deleteInvented | keepBoth | unsure |
|---|---|---|---|---|---|---|
| 1-medium | 6 | 0 | 0 | 0 | 3 | 5 |
| 2-code-collision | 4 | 0 | 1 | 22 | 38 | 4 |
| 3-code-only-stub | 0 | 8 | 0 | 0 | 0 | 0 |
| 4-unique-toys-subtitle | 0 | 0 | 13 | 0 | 0 | 0 |
| 5-name-only | 28 | 0 | 0 | 0 | 7 | 5 |
| 6-other-low | 1 | 0 | 2 | 0 | 21 | 4 |

## Unsure (need a decision)

- Studio Series SS-35 Leader Class Jetfire Jet Fire (Show.Z #1273) vs `d14ss-tlk-megatron`: Show.Z calls this Takara but uses the Hasbro number (Hasbro 35 Jetfire ROTF / 34 Megatron DOTM / 10 Jazz; Takara SS-35 is KSI Boss, SS-34 Long Haul, SS-09 Jazz). Unclear whether it is the Takara or the Hasbro unit. The paired proper row is not the same character anyway (d14ss numbering is invented; see provenance flags).
- Studio Series 34 SS34 SS-34 Leader Class Megatron (Show.Z #1275) vs `d14ss-tlk-optimus`: Show.Z calls this Takara but uses the Hasbro number (Hasbro 35 Jetfire ROTF / 34 Megatron DOTM / 10 Jazz; Takara SS-35 is KSI Boss, SS-34 Long Haul, SS-09 Jazz). Unclear whether it is the Takara or the Hasbro unit. The paired proper row is not the same character anyway (d14ss numbering is invented; see provenance flags).
- Studio Series SS11 SS-11 Deluxe Class Lockdown (Show.Z #0813) vs `d14ss-aoe-lockdown`: Takara Studio Series is a separate release from Hasbro (keep apart), but this Show.Z listing uses the Hasbro number: Takara numbering is SS-09 Jazz, SS-10 Lockdown, SS-11 Megatron (ROTF), SS-15 Ironhide. Cannot tell whether Show.Z sold the Takara or Hasbro unit. The paired d14ss-* Hasbro row also carries invented movie/number labels (see provenance flags).
- Studio Series SS10 SS-10 Deluxe Class Jazz (Show.Z #0814) vs `tfc-shockwave-ss10`: Show.Z calls this Takara but uses the Hasbro number (Hasbro 35 Jetfire ROTF / 34 Megatron DOTM / 10 Jazz; Takara SS-35 is KSI Boss, SS-34 Long Haul, SS-09 Jazz). Unclear whether it is the Takara or the Hasbro unit. The paired proper row is not the same character anyway (d14ss numbering is invented; see provenance flags).
- Studio Series SS14 SS-14 Voyager Class Ironhide (Show.Z #0849) vs `d14ss-dotm-ironhide`: Takara Studio Series is a separate release from Hasbro (keep apart), but this Show.Z listing uses the Hasbro number: Takara numbering is SS-09 Jazz, SS-10 Lockdown, SS-11 Megatron (ROTF), SS-15 Ironhide. Cannot tell whether Show.Z sold the Takara or Hasbro unit. The paired d14ss-* Hasbro row also carries invented movie/number labels (see provenance flags).
- Studio Series SS13 SS-13 Voyager Class Megatron (Show.Z #0742) vs `d14ss-dotm-megatron`: Takara Studio Series is a separate release from Hasbro (keep apart), but this Show.Z listing uses the Hasbro number: Takara numbering is SS-09 Jazz, SS-10 Lockdown, SS-11 Megatron (ROTF), SS-15 Ironhide. Cannot tell whether Show.Z sold the Takara or Hasbro unit. The paired d14ss-* Hasbro row also carries invented movie/number labels (see provenance flags).
- 3Z1046 Transformers DLX Jazz Deluxe Version (Show.Z #7304) vs `tz7-46`: See 3Z0900: tz7-46 sku is 3Z1046 (Deluxe Version) but it also aliases standard 3Z0900 and MDLX 3Z0338.
- Kuro Kara Kuri Ultra Magnus (Show.Z #6095) vs `ft6-ft-kkk-ultra-magnus`: Character matches, but ft6-ft-kkk-ultra-magnus comes from the ft6 Kuro Kara Kuri batch (curated-bbts-wave6): no SKU, release dates two months apart, round MSRPs, and several characters with no known KKK release. Audit the batch before merging real listings into it.
- 3Z0900 Transformers DLX Jazz (Show.Z #7303) vs `tz7-46`: tz7-46 is conflated: sku 3Z10460W0 (= 3Z1046 DLX Jazz Deluxe Version) but aliases 3Z09000W0 (standard DLX Jazz) and 3Z0338 (MDLX Jazz). Needs a decision on which release tz7-46 represents.
- 3Z0202 Transformers War for Cybertron Trilogy DLX Optimus Prime (Show.Z #6866) vs `tz3-dlx-prime-one`: tz3-dlx-prime-one is named "Transformers One DLX" but its EAN 4897056203204 + image are the War for Cybertron DLX Optimus Prime (= 3Z0202). Could be a merge after tz3-dlx-prime-one is renamed; not proposed without a direct EAN→3Z0202 source.
- Bumblebee Shockwave Pre-Assembled Model Kit (Show.Z #6420) vs `sf-yolopark-amk-pro-bumblebee2018-shockwave`: Two Show.Z AMK Pro Bumblebee-film Shockwave listings (#6420 from 2024-07 and #8078, a 2026 pre-order). #8078 is merged into the 2026 proper row; #6420 may be the original 2024 run or a duplicate listing.
- 3Z0850 MDLX Transformers One Elita (Show.Z #6529) vs `tz3-dlx-elita`: tz3-dlx-elita "Transformers One DLX Elita-1" aliases 3Z0850 (MDLX Elita). Unclear whether a DLX Elita exists or the row is the MDLX mislabelled.
- Kuro Kara Kuri Starscream (Show.Z #6097) vs `ft6-ft-kkk-starscream`: Character matches, but ft6-ft-kkk-starscream comes from the ft6 Kuro Kara Kuri batch (curated-bbts-wave6): no SKU, release dates two months apart, round MSRPs, and several characters with no known KKK release. Audit the batch before merging real listings into it.
- Kuro Kara Kuri 04SG Shattered Glass Optimus Prime (Show.Z #2933) vs `ft6-ft-kkk-optimus-movie`: KKK 04SG Shattered Glass is a variant; the paired ft6-ft-kkk-optimus-movie is from the templated ft6 batch.
- X Hasbro DLX The Last Knight Bumblebee (Show.Z #2671) vs `afmon-threezero-bumblebee-th3z0164`: Show.Z lists the 2020 DLX TLK Bumblebee. afmon-threezero-bumblebee-th3z0164 is a 2026-09 EE listing (TH3Z0164) that may be a reissue. Release year unclear.
- Kuro Kara Kuri 04 Optimus Prime (Show.Z #1950) vs `ft6-ft-kkk-optimus-movie`: Character matches, but ft6-ft-kkk-optimus-movie comes from the ft6 Kuro Kara Kuri batch (curated-bbts-wave6): no SKU, release dates two months apart, round MSRPs, and several characters with no known KKK release. Audit the batch before merging real listings into it.
- Kuro Kara Kuri Drift Reissue (Show.Z #0289) vs `ft6-ft-kkk-drift`: KKK Drift Reissue (2017) vs ft6-ft-kkk-drift (templated ft6 batch, date 2024-04).
- D-15 Kukinski Dead End G2 Version (Show.Z #5921) vs `dx96-dx9-w-24`: dx96-dx9-w-24 is a code-only "D15" template row filed under "War in Pocket" (curated-bbts-wave6). DX9 D-15 is Kukinski; the Show.Z row is the G2 variant, so it is not a merge either way. Leave for a wave6 batch audit.

## Provenance flags (out of scope, not changed)

- d14ss-* (109 rows, curated-densify): Studio Series numbers/film labels are invented, and several rows carry SKUs/images of other products (e.g. d14ss-aoe-crosshairs "SS-07 AOE" = Hasbro 92 TLK Crosshairs; d14ss-dotm-megatron UPC 630509652204 = Hasbro 13 ROTF Megatron; d14ss-tlk-megatron "SS-35" but Hasbro 35 is ROTF Jetfire). Needs its own audit against https://tfwiki.net/wiki/Studio_Series.
- na-h10..na-h55 (curated-bbts-wave4): the rest of the NewAge batch is also mostly invented (e.g. na-h13 "Lucifer / H13 Starscream" is right, but na-h14 "Leviathan / H14 Skywarp" should be Thundercracker, na-h10 "Abadon / H10 Runabout" should be Kickback). Out of scope here.
- dw6-* (curated-bbts-wave6), xt6-* (MX-03..MX-30, "Combiner Limb", "Chrome Exclusive"), dx96-* (K4..K10, "War in Pocket" names), ft6-ft-kkk-*: templated sequential batches. Stub MSRPs are flat ($110 for every MX, $75 for every K). Recommend the date-audit invented-row pass covers waves 4 and 6 next.
- threezero rows tz9-tz-13/14/15, tz3-dlx-prime-one, tz7-46, tz-bumblebee-dlx carry polluted alias lists (up to 14 different 3Z codes per row). Alias cleanup not proposed without per-code sources.
