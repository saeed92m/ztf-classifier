#!/usr/bin/env python3
"""Full-parent CPVS raw-row and SNR reconstruction audit; research only."""
from __future__ import annotations
import argparse, array, csv, hashlib, json, math, subprocess, zipfile, zlib
from pathlib import Path
from typing import Any

LN10_OVER_2P5=math.log(10.0)/2.5
SNR_FACTOR=1.0857362047581296
THRESHOLDS={"g":2.5,"r":3.0}
MAX_SEQ=781604
EXPECTED={"parent":781602,"table4":730184,"candidate":741786,"residual":11602,"four_field_only":55}
PARENT_HASHES={
 "parent_metadata.tsv":("3675b1274f73fcb15d47e7a780f194ef8fa335cd248c6ff53ea4f01559c86591",94367016),
 "selected.tsv":("699ff34bcf8dd4b5043eed48384973cb5109fd86ca260f831a502097370238df",5085593),
 "selection_diagnostics.json":("7e763d8804a57d75d1633d0a4089a4a6ac5aa40bb4695964d35e645b67ad5b61",11700390),
 "membership_audit.json":("4c1a082569820af26cbca80320a4913a00e1849446b0ca0205fc872b5ce89c5c",1004),
}
RECON_HASHES={
 "table2.dat":("2c77c5b6c14811f6abab6e1442ce82c6fb54dbdcfc141954165704fecfcb3881",178986858),
 "table4_to_table2_seq_crosswalk.tsv":("89d353b3b8ce24b60ab69df3e119a8e7b7832c3271fcad950cbbd743921349aa",30455719),
 "four_field_only_55.tsv":("b7f712910467616919f616dfd5f9ddb94a4c6b819f973469eeeb704fae0e1ab6",7063),
}
ARCHIVES={
 "g":{"member":"ztf2g","sha":"47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9","member_sha":"366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16","size":5034066142,"rows":89697393,"crc":"d2f33aa0"},
 "r":{"member":"ztf2r","sha":"48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74","member_sha":"78df6d0b22099a7e5c6e74b897682c6ab94f90d5f9e887d4b0b3b152514e50fe","size":6175667360,"rows":109971576,"crc":"225495a0"},
}
COUNT_FIELDS=("raw","valid","flag_ne","flag_lt","flag_zero","snr_approx","snr_exact","snr_inverse","snr_exact_ne","snr_exact_lt","snr_exact_zero")

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()

def verify(path:Path,expected:str,size:int)->dict[str,Any]:
 actual=sha(path)
 if path.stat().st_size!=size or actual!=expected: raise ValueError(f"Hash/size mismatch: {path}")
 return {"bytes":size,"sha256":actual}

def pos(v:Any)->bool:
 try: x=float(v)
 except (TypeError,ValueError): return False
 return math.isfinite(x) and x>0

def load_inputs(parent_dir:Path,recon_dir:Path):
 root=parent_dir/"ztf_periodic_730k"
 verified={}
 for name,(digest,size) in PARENT_HASHES.items(): verified[name]=verify(root/name,digest,size)
 for name,(digest,size) in RECON_HASHES.items():
  rel=(Path("raw")/name) if name=="table2.dat" else (Path("output")/name)
  verified[name]=verify(recon_dir/rel,digest,size)
 table2={}
 with (recon_dir/"raw"/"table2.dat").open("r",encoding="ascii") as f:
  for n,line in enumerate(f,1):
   p=line.split()
   if len(p)!=27: raise ValueError(f"Table2 row {n}: expected 27 fields, got {len(p)}")
   sid=int(p[1])
   if sid in table2: raise ValueError(f"Duplicate Table2 Seq {sid}")
   table2[sid]={"ZTF":p[0],"Type":p[24],"Per":float(p[4]),"gmag":p[8],"rmag":p[9],"Per-g":p[10],"Per-r":p[11],"Ng":int(p[12]),"Nr":int(p[13]),"gAmp":p[20],"rAmp":p[21]}
 if len(table2)!=EXPECTED["parent"]: raise ValueError("Table2 row count mismatch")
 candidate=set()
 with (root/"selected.tsv").open("r",encoding="utf-8-sig",newline="") as f:
  for r in csv.DictReader(f,delimiter="\t"): candidate.add(int(r["SourceID"]))
 diag=json.loads((root/"selection_diagnostics.json").read_text(encoding="utf-8"))
 residual={int(r["source_id"]) for r in diag["candidate_only_all_objects"]}
 table4=set()
 with (recon_dir/"output"/"table4_to_table2_seq_crosswalk.tsv").open("r",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f,delimiter="\t"):
   sid=int(r["Table2_Seq"])
   if sid in table4: raise ValueError("Duplicate Table4 crosswalk ID")
   if r["Table4_ID_equals_Table2_Seq"].lower()!="true": raise ValueError("Table4/Table2 ID crosswalk mismatch")
   table4.add(sid)
 controls=set()
 with (recon_dir/"output"/"four_field_only_55.tsv").open("r",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f,delimiter="\t"):
   sid=int(r["SourceID"])
   if r["four_field_positive"].lower()!="true": raise ValueError("Invalid 55-control predicate")
   controls.add(sid)
 if (len(candidate),len(residual),len(table4),len(controls))!=(EXPECTED["candidate"],EXPECTED["residual"],EXPECTED["table4"],EXPECTED["four_field_only"]): raise ValueError("Membership counts do not match pinned evidence")
 if candidate-table4!=residual or table4-candidate: raise ValueError("Candidate/Table4/residual partition mismatch")
 if controls & (candidate|table4): raise ValueError("Four-field-only controls overlap candidates")
 if not controls<=set(table2): raise ValueError("Unknown four-field-only control ID")
 membership=json.loads((root/"membership_audit.json").read_text())
 if membership["published_only_count"]!=0 or membership["published_count"]!=EXPECTED["table4"]: raise ValueError("Membership audit failed")
 return table2,candidate,table4,residual,controls,{"verified_inputs":verified,"membership_audit":membership}

def resolve_member_name(archive:zipfile.ZipFile, basename:str)->str:
 matches=[name for name in archive.namelist() if Path(name).name==basename and "__MACOSX" not in name]
 if len(matches)!=1: raise ValueError(f"Expected one {basename} member by basename; found {matches}")
 return matches[0]

def scan(path:Path,band:str,parent_ids:set[int]):
 cfg=ARCHIVES[band]
 if sha(path)!=cfg["sha"]: raise ValueError(f"{band} archive SHA-256 mismatch")
 with zipfile.ZipFile(path) as z:
  member_name=resolve_member_name(z,cfg["member"])
 counts={k:array.array("I",[0])*(MAX_SEQ+1) for k in COUNT_FIELDS}
 digest=hashlib.sha256(); crc=0; nbytes=0; nrows=0; malformed=0; unknown=0; missing_flag=0
 p=subprocess.Popen(["unzip","-p",str(path),member_name],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert p.stdout is not None
 for line in p.stdout:
  digest.update(line); crc=zlib.crc32(line,crc); nbytes+=len(line); nrows+=1
  fields=line.strip().replace(b",",b" ").split()
  if len(fields)!=7: malformed+=1; continue
  try: sid=int(fields[0])
  except ValueError: malformed+=1; continue
  if sid not in parent_ids: unknown+=1; continue
  counts["raw"][sid]+=1
  try:
   mjd=float(fields[3]); mag=float(fields[4]); err=float(fields[5])
   valid=math.isfinite(mjd) and math.isfinite(mag) and mag!=0 and math.isfinite(err) and err>0
  except ValueError: valid=False; err=float("nan")
  if not valid: continue
  counts["valid"][sid]+=1
  try: flag=int(fields[6])
  except ValueError: flag=None
  if flag is None: missing_flag+=1
  else:
   if flag!=32768: counts["flag_ne"][sid]+=1
   if flag<32768: counts["flag_lt"][sid]+=1
   if flag==0: counts["flag_zero"][sid]+=1
  approx=SNR_FACTOR/err; inv=1.0/err; expv=err*LN10_OVER_2P5
  exact=1.0/math.expm1(expv) if expv<700 else 0.0
  threshold=THRESHOLDS[band]
  if approx>=threshold: counts["snr_approx"][sid]+=1
  if inv>=threshold: counts["snr_inverse"][sid]+=1
  if exact>=threshold:
   counts["snr_exact"][sid]+=1
   if flag is not None and flag!=32768: counts["snr_exact_ne"][sid]+=1
   if flag is not None and flag<32768: counts["snr_exact_lt"][sid]+=1
   if flag==0: counts["snr_exact_zero"][sid]+=1
 stderr=p.stderr.read() if p.stderr else b""; rc=p.wait()
 if rc: raise RuntimeError(stderr.decode(errors="replace")[-2000:])
 if nrows!=cfg["rows"] or nbytes!=cfg["size"] or digest.hexdigest()!=cfg["member_sha"] or f"{crc&0xffffffff:08x}"!=cfg["crc"]: raise ValueError(f"{band} member integrity mismatch")
 return counts,{"archive_sha256":cfg["sha"],"member_sha256":digest.hexdigest(),"member_crc32":f"{crc&0xffffffff:08x}","member_bytes":nbytes,"member_rows":nrows,"malformed_rows":malformed,"unknown_source_id_rows":unknown,"valid_rows_missing_flag":missing_flag,"unique_ids_with_rows":sum(v>0 for v in counts["raw"]),"unique_ids_with_valid_rows":sum(v>0 for v in counts["valid"])}

def confusion(candidate:set[int],reference:set[int])->dict[str,Any]:
 tp=len(candidate&reference); fp=len(candidate-reference); fn=len(reference-candidate)
 return {"candidate_count":len(candidate),"TP":tp,"FP":fp,"FN":fn,"precision":tp/(tp+fp) if tp+fp else None,"recall":tp/(tp+fn) if tp+fn else None}

def cohort(sid:int,t4:set[int],res:set[int],controls:set[int])->str:
 if sid in t4:return "table4_member"
 if sid in res:return "candidate_only_residual"
 if sid in controls:return "four_field_only_55"
 return "other_parent"

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--parent-dir",type=Path,required=True); ap.add_argument("--reconciliation-dir",type=Path,required=True)
 ap.add_argument("--g-archive",type=Path,required=True); ap.add_argument("--r-archive",type=Path,required=True); ap.add_argument("--output-dir",type=Path,required=True)
 a=ap.parse_args()
 table2,candidate,t4,residual,controls,input_meta=load_inputs(a.parent_dir,a.reconciliation_dir)
 parent=set(table2)
 raw={}; raw_meta={}
 for band,path in (("g",a.g_archive),("r",a.r_archive)): raw[band],raw_meta[band]=scan(path,band,parent)
 core=set(); six=set(); proxy=set()
 for sid,row in table2.items():
  c=all(pos(row[k]) for k in ("gmag","rmag","Per-g","Per-r"))
  s=c and all(pos(row[k]) for k in ("gAmp","rAmp"))
  if c: core.add(sid)
  if s: six.add(sid)
  if s and row["Ng"]>0 and row["Nr"]>0: proxy.add(sid)
 metadata_results={
  "four_core_positive":{"parent":confusion(core,t4),"candidate_intersection":confusion(core&candidate,t4)},
  "six_explicit_missing_fields_positive":{"parent":confusion(six,t4),"candidate_intersection":confusion(six&candidate,t4)},
  "six_fields_plus_positive_Ng_Nr":{"parent":confusion(proxy,t4),"candidate_intersection":confusion(proxy&candidate,t4)},
 }
 policies={"approximate_all_valid":"snr_approx","exact_all_valid":"snr_exact","inverse_error_all_valid":"snr_inverse","exact_flag_ne_32768":"snr_exact_ne","exact_flag_lt_32768":"snr_exact_lt","exact_flag_zero":"snr_exact_zero"}
 snr_sets={}
 for name,field in policies.items():
  snr_sets[name]={sid for sid in parent if raw["g"][field][sid]>0 and raw["r"][field][sid]>0}
 policy_results={name:{"vs_reconstructed_candidate":confusion(ids,candidate),"vs_Table4":confusion(ids,t4),"and_four_core_vs_Table4":confusion(ids&core,t4)} for name,ids in snr_sets.items()}
 count_results={}
 for band,expected_field in (("g","Ng"),("r","Nr")):
  count_results[band]={}
  for group in ("table4_member","candidate_only_residual","four_field_only_55","other_parent"):
   ids=[sid for sid in parent if cohort(sid,t4,residual,controls)==group]
   expected=[table2[sid][expected_field] for sid in ids]; observed=[raw[band]["raw"][sid] for sid in ids]
   count_results[band][group]={"objects":len(ids),"table2_positive":sum(v>0 for v in expected),"raw_present":sum(v>0 for v in observed),"exact_matches":sum(x==y for x,y in zip(expected,observed)),"raw_less":sum(x<y for x,y in zip(observed,expected)),"raw_greater":sum(x>y for x,y in zip(observed,expected)),"table2_positive_raw_zero":sum(x>0 and y==0 for x,y in zip(expected,observed)),"table2_zero_raw_positive":sum(x==0 and y>0 for x,y in zip(expected,observed))}
 a.output_dir.mkdir(parents=True,exist_ok=True)
 cols=["SourceID","ZTF","Type","cohort","Ng","Nr","raw_g","raw_r","valid_g","valid_r","g_flag_ne","r_flag_ne","g_flag_lt","r_flag_lt","g_flag_zero","r_flag_zero","g_snr_approx","r_snr_approx","g_snr_exact","r_snr_exact","g_snr_inverse","r_snr_inverse","g_snr_exact_flag_ne","r_snr_exact_flag_ne","g_snr_exact_flag_lt","r_snr_exact_flag_lt","g_snr_exact_flag_zero","r_snr_exact_flag_zero","four_core_positive","six_fields_positive","Table4_member","candidate_member"]
 all_path=a.output_dir/"cpvs_full_parent_object_reconciliation.tsv"; mismatch_path=a.output_dir/"cpvs_full_parent_rowcount_mismatches.tsv"
 mismatch_n=0
 with all_path.open("w",encoding="utf-8",newline="") as fa,mismatch_path.open("w",encoding="utf-8",newline="") as fm:
  wa=csv.DictWriter(fa,fieldnames=cols,delimiter="\t"); wm=csv.DictWriter(fm,fieldnames=cols,delimiter="\t"); wa.writeheader(); wm.writeheader()
  for sid,row in table2.items():
   g=raw["g"]; r=raw["r"]
   rec={"SourceID":sid,"ZTF":row["ZTF"],"Type":row["Type"],"cohort":cohort(sid,t4,residual,controls),"Ng":row["Ng"],"Nr":row["Nr"],
    "raw_g":g["raw"][sid],"raw_r":r["raw"][sid],"valid_g":g["valid"][sid],"valid_r":r["valid"][sid],
    "g_flag_ne":g["flag_ne"][sid],"r_flag_ne":r["flag_ne"][sid],"g_flag_lt":g["flag_lt"][sid],"r_flag_lt":r["flag_lt"][sid],"g_flag_zero":g["flag_zero"][sid],"r_flag_zero":r["flag_zero"][sid],
    "g_snr_approx":g["snr_approx"][sid],"r_snr_approx":r["snr_approx"][sid],"g_snr_exact":g["snr_exact"][sid],"r_snr_exact":r["snr_exact"][sid],"g_snr_inverse":g["snr_inverse"][sid],"r_snr_inverse":r["snr_inverse"][sid],
    "g_snr_exact_flag_ne":g["snr_exact_ne"][sid],"r_snr_exact_flag_ne":r["snr_exact_ne"][sid],"g_snr_exact_flag_lt":g["snr_exact_lt"][sid],"r_snr_exact_flag_lt":r["snr_exact_lt"][sid],"g_snr_exact_flag_zero":g["snr_exact_zero"][sid],"r_snr_exact_flag_zero":r["snr_exact_zero"][sid],
    "four_core_positive":sid in core,"six_fields_positive":sid in six,"Table4_member":sid in t4,"candidate_member":sid in candidate}
   wa.writerow(rec)
   if rec["raw_g"]!=row["Ng"] or rec["raw_r"]!=row["Nr"]: wm.writerow(rec); mismatch_n+=1
 report={"schema_version":"1.0","diagnostic":"Full-parent CPVS raw-row, SNR and metadata reconstruction","scope":"All 781,602 Table2 objects; research-only; no production selector changes",
  "inputs":input_meta,"raw_archives":raw_meta,
  "membership_partition":{"parent":len(parent),"Table4":len(t4),"candidate":len(candidate),"candidate_only":len(residual),"four_field_only_55":len(controls),"other_parent":len(parent-t4-residual-controls),"candidate_equals_Table4_union_residual":candidate==t4|residual},
  "metadata_completeness":metadata_results,"SNR_policy_comparison":policy_results,"raw_count_comparison_by_cohort":count_results,"rowcount_mismatch_objects":mismatch_n,
  "flag_semantics_warning":"Zenodo flag is not proven equivalent to DR2 catflags. !=32768, <32768 and ==0 are diagnostics only.",
  "limitations":["Raw attachments do not contain image-level INFOBITS.","Missing raw rows do not prove low SNR; verify archive completeness and SourceID/coordinate mapping.","Table2 Ng/Nr may represent a different processing stage than Zenodo attachment row counts.","An exact membership match is empirical evidence, not proof of publisher intent."],
  "outputs":{"object_reconciliation":all_path.name,"rowcount_mismatches":mismatch_path.name}}
 report_path=a.output_dir/"cpvs_full_parent_reconstruction_report.json"
 report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 for p in (report_path,all_path,mismatch_path): print(f"{p.name} bytes={p.stat().st_size} sha256={sha(p)}")
 print(json.dumps(report["membership_partition"],indent=2)); print(json.dumps(policy_results,indent=2)); print(json.dumps(count_results,indent=2))
if __name__=="__main__": main()
