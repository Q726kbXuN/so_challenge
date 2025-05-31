
import random,re,sys
def baby(x):
 x=x.lower()
 x=re.sub(r'[lr]','w',x)
 x=re.sub(r'th','d',x)
 x=re.sub(r'n(?=\w)','ny',x)
 if len(x)<=4 and random.random()<0.3:
  x=f"{x}-{x}"
 return x.capitalize() if x[0].isupper() else x
print(''.join(baby(x) if x.isalpha() else x for x in re.findall(r'\w+|\W+',sys.stdin.read())))
