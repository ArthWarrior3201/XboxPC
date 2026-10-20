const button=document.getElementById('download');
const status=document.getElementById('download-status');
(async()=>{
 try {
  const config=await fetch('assets/config.json').then(r=>r.json());
  button.href=`https://github.com/${config.repository}/releases/latest/download/${encodeURIComponent(config.releaseAsset)}`;
  const response=await fetch(`https://api.github.com/repos/${config.repository}/releases/latest`);
  if(response.status===404){status.textContent='The first release has not been published yet.';return;}
  if(!response.ok)throw Error();
  const release=await response.json();
  const asset=release.assets.find(a=>a.name===config.releaseAsset);
  status.textContent=asset?`${release.tag_name} · ZIP`:`Upload ${config.releaseAsset} to the latest release.`;
 }catch{status.textContent='Latest release · ZIP';}
})();
