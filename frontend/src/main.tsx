import React from 'react'
import { createRoot } from 'react-dom/client'

function App(){
    const [q, setQ] = React.useState('summary bone density')
    const [res, setRes] = React.useState<any[]>([])
    const [loading, setLoading] = React.useState(false)
    const [error, setError] = React.useState<string | null>(null)

    const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

    const search = async () => {
        setLoading(true)
        setError(null)
        try {
            const API_BASE = import.meta.env.VITE_API_URL || "http://backend:8000";
            const r = await fetch(`${API_BASE}/api/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: q, topk: 10, hybrid: true })
            })
            if (!r.ok) throw new Error(`HTTP ${r.status}`)
            const j = await r.json()
            setRes(j.results || [])
            if ((j.results || []).length === 0) setError('No results found.')
        } catch(e:any) {
            console.error(e)
            setError('Search failed. Please check backend or network.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{fontFamily:'sans-serif', padding:20}}>
            <h1>Space Biology Knowledge Engine</h1>
            <p>Hybrid search across pgvector (rich) and qdrant (summaries). Use "summary" to bias toward summaries. Optional keyword filter: kw:bone</p>

            <div style={{display:'flex', gap:8, marginBottom:12}}>
                <input
                    style={{flex:1, padding:8}}
                    value={q}
                    onChange={e=>setQ(e.target.value)}
                    placeholder="Type a query..."
                    onKeyDown={e=>e.key === 'Enter' && search()}
                />
                <button onClick={search} disabled={loading}>
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </div>

            {error && (
                <div style={{color:'gray', marginBottom:12}}>
                    {error}
                </div>
            )}

            <ul>
                {res.map((r,i)=>(
                    <li key={i} style={{marginBottom:12}}>
                        <strong>[{r.source}]</strong>{' '}
                        <a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}</a><br/>
                        <small>score: {r.score?.toFixed(3)}</small>
                        <div>{r.summary || r.snippet}</div>
                    </li>
                ))}
            </ul>
        </div>
    )
}

createRoot(document.getElementById('root')!).render(<App/>)
