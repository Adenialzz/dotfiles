function git_file_count() {
  git status --porcelain \
  | awk '
  {
    file=$2
    n=split(file,a,".")
    ext=(n>1?a[n]:"(no_ext)")
    cnt[ext]++
  }
  END {
    for (e in cnt)
      printf "%-10s %d\n", e, cnt[e]
  }'
}