"""Small local launcher; all scans run off the UI thread."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from .library import snapshot, launch

def main():
    root=tk.Tk(); root.title('XboxPC v1'); root.geometry('900x540')
    ttk.Label(root,text='XboxPC v1',font=('Segoe UI',24,'bold')).pack(anchor='w',padx=20,pady=(16,4))
    ttk.Label(root,text='Installed PC library • no account linking • native store launches').pack(anchor='w',padx=20)
    ttk.Label(root,text='Xbox console translation remains experimental and does not run commercial games.').pack(anchor='w',padx=20,pady=(4,12))
    tree=ttk.Treeview(root,columns=('store','title'),show='headings',selectmode='browse')
    tree.heading('store',text='Store'); tree.heading('title',text='Installed title')
    tree.column('store',width=110,stretch=False); tree.column('title',width=650)
    tree.pack(fill='both',expand=True,padx=20)
    status=tk.StringVar(value='Ready'); ttk.Label(root,textvariable=status,wraplength=850).pack(anchor='w',padx=20,pady=8)
    messages=tk.Text(root,height=4,wrap='word'); messages.pack(fill='x',padx=20)
    bar=ttk.Frame(root); bar.pack(fill='x',padx=20,pady=12)
    jobs=queue.Queue(); busy=False
    def work(kind,fn):
        nonlocal busy
        if busy:return
        busy=True; refresh.configure(state='disabled'); play.configure(state='disabled'); status.set('Refreshing local library…')
        def run():
            try: jobs.put((kind,fn(),None))
            except Exception as e: jobs.put((kind,None,str(e)))
        threading.Thread(target=run,daemon=True).start()
    def selected():
        ids=tree.selection()
        if not ids: messagebox.showinfo('XboxPC','Select an installed title first.'); return
        work('launch',lambda:launch(ids[0]))
    def poll():
        nonlocal busy
        try: kind,result,error=jobs.get_nowait()
        except queue.Empty: root.after(100,poll); return
        busy=False; refresh.configure(state='normal'); play.configure(state='normal')
        if error: status.set(error)
        elif kind=='scan':
            tree.delete(*tree.get_children())
            for g in result['games']: tree.insert('', 'end',iid=g['key'],values=(g['store'].title(),g['name']))
            status.set(f"{len(result['games'])} installed titles • refreshed {result['refreshed_at']}")
            messages.delete('1.0','end'); messages.insert('1.0','\n'.join(result['warnings']))
        else: status.set(result['note'])
        root.after(100,poll)
    refresh=ttk.Button(bar,text='Refresh library',command=lambda:work('scan',snapshot)); refresh.pack(side='left')
    play=ttk.Button(bar,text='Refresh & launch selected',command=selected); play.pack(side='right')
    root.after(100,poll); work('scan',snapshot); root.mainloop()
if __name__=='__main__':main()
