/* Preserve ordinary JSON/CSV fetches and downloads while storing exact bytes as gzip. */
(()=>{'use strict';
  if(window.overtakeData)return;
  const base=new URL('../',document.currentScript.src),nativeFetch=window.fetch.bind(window);
  let registry;
  const routes=()=>registry||(registry=nativeFetch(new URL('_data/index.json.gz',base),{cache:'no-cache'})
    .then(async r=>{if(!r.ok)throw Error('Data register: '+r.status);return JSON.parse(await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).text());})
    .catch(e=>{registry=null;throw e;}));
  const key=url=>url.origin===base.origin&&url.pathname.startsWith(base.pathname)?decodeURIComponent(url.pathname.slice(base.pathname.length)):null;
  const originalURL=input=>new URL(input instanceof Request?input.url:String(input),document.baseURI);
  const read=async(input,init)=>{
    const url=originalURL(input),name=key(url),method=init?.method||(input instanceof Request?input.method:'GET');
    if(!name||!/\.(json|csv)$/i.test(name)||method.toUpperCase()!=='GET')return nativeFetch(input,init);
    const entries=await routes();
    if(!entries[name])return nativeFetch(input,init);
    const packed=new URL(url);packed.pathname+='.gz';
    const request=input instanceof Request?new Request(packed,new Request(input,init)):new Request(packed,init);
    const response=await nativeFetch(request);
    if(!response.ok)return response;
    const headers=new Headers(response.headers);headers.delete('content-encoding');headers.delete('content-length');
    headers.set('content-type',name.endsWith('.json')?'application/json; charset=utf-8':'text/csv; charset=utf-8');
    const decoded=new Response(response.body.pipeThrough(new DecompressionStream('gzip')),{status:response.status,statusText:response.statusText,headers});
    Object.defineProperty(decoded,'url',{value:url.href});return decoded;
  };
  window.fetch=read;
  window.overtakeData={base,read,key,routes};
  const download=async(name,filename)=>{
    const response=await read(new URL(name,base));if(!response.ok)throw Error('Download: '+response.status);
    const blob=await response.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download=filename||name.split('/').pop();a.click();setTimeout(()=>URL.revokeObjectURL(url),60000);
  };
  // Rewrite links after the register loads, including links added inside popups.
  const update=async()=>{
    const entries=await routes();
    document.querySelectorAll('a[href]').forEach(a=>{
      if(a.dataset.f1Data)return;
      const name=key(new URL(a.href));if(!name||!entries[name])return;
      a.dataset.f1Data=name;
      a.href=new URL('_data/view.html',base).href+'#path='+encodeURIComponent(name);
    });
  };
  document.addEventListener('click',e=>{
    const a=e.target.closest?.('a[data-f1-data]');
    if(!a||e.defaultPrevented||e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
    if(a.hasAttribute('download')||a.dataset.f1Data.endsWith('.csv')){
      e.preventDefault();download(a.dataset.f1Data,a.getAttribute('download')).catch(error=>alert(error.message));
    }
  });
  const start=()=>{update().catch(console.error);new MutationObserver(()=>update().catch(console.error)).observe(document.body,{childList:true,subtree:true});};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
