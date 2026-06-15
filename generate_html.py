import sqlite3

def generer_html():
    db = sqlite3.connect('annonces.db')
    # On ajoute url_source pour pouvoir cliquer sur les annonces
    annonces = db.execute('SELECT titre, prix_entier, localisation_brute, urls_images, url_source FROM annonces').fetchall()
    
    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Immotrust - Comparateur</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #0071C2; /* Bleu type Trivago / Booking */
                --secondary: #F3F4F5;
                --text-main: #222222;
                --text-muted: #5e6d77;
                --accent: #00A698;
                --card-bg: #FFFFFF;
            }
            body { 
                font-family: 'Inter', sans-serif; 
                background-color: var(--secondary); 
                margin: 0; 
                padding: 0; 
                color: var(--text-main);
            }
            header {
                background: white;
                padding: 20px 40px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                display: flex;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            header h1 { margin: 0; color: var(--primary); font-size: 26px; }
            .container { max-width: 1000px; margin: 40px auto; padding: 0 20px; }
            
            /* Design de la carte façon Trivago */
            .card { 
                background: var(--card-bg); 
                border-radius: 12px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.04); 
                display: flex; 
                margin-bottom: 20px; 
                overflow: hidden;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                height: 220px;
                border: 1px solid #e0e0e0;
            }
            .card:hover {
                transform: translateY(-4px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.12);
            }
            .card-img-container {
                width: 300px;
                flex-shrink: 0;
                display: flex;
                overflow-x: auto;
                scroll-snap-type: x mandatory;
                scrollbar-width: none; /* Cache barre Firefox */
            }
            .card-img-container::-webkit-scrollbar { display: none; } /* Cache barre Chrome */
            .card img { 
                width: 300px; 
                height: 100%; 
                flex-shrink: 0;
                object-fit: cover;
                scroll-snap-align: start;
                transition: transform 0.5s ease;
            }
            
            .card-content { 
                padding: 20px 25px; 
                display: flex; 
                flex-direction: column; 
                justify-content: space-between;
                flex-grow: 1;
            }
            .title { font-size: 1.3em; font-weight: 700; margin: 0 0 8px 0; color: var(--text-main); }
            .loc { color: var(--text-muted); font-size: 0.9em; margin: 0; display: flex; align-items: center; }
            
            .price-container { text-align: right; }
            .price-label { font-size: 0.85em; color: var(--text-muted); margin: 0;}
            .prix { color: #d32f2f; font-weight: 700; font-size: 1.5em; margin: 3px 0 0 0; }
            
            .footer { display: flex; justify-content: space-between; align-items: flex-end; }
            
            .btn {
                background: var(--accent);
                color: white;
                text-decoration: none;
                padding: 12px 28px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 0.95em;
                transition: background 0.3s;
                text-align: center;
            }
            .btn:hover { background: #008f82; }
            
        </style>
    </head>
    <body>
        <header>
            <h1>🏢 Immotrust Agrégateur</h1>
        </header>
        <div class="container">
    """
    
    for row in annonces:
        titre, prix, loc, images, url = row
        
        # Gestion des multiples images (carrousel avec scroll horizontal)
        images_html = ""
        if images:
            for img in images.split(','):
                img = img.strip()
                if not img: continue
                if "http" not in img:
                    img = "https://mapiole.com" + img # Sécurité URLs relatives
                images_html += f'<img src="{img}" alt="Photo annonce">'
        else:
            images_html = '<img src="https://via.placeholder.com/300x200?text=Pas+d+image+fournie" alt="Aucune photo">'
            
        # Format du prix avec séparateur de milliers
        prix_format = f"{prix:,}".replace(",", " ") if prix else "N/A "
        
        html += f"""
        <div class="card">
            <div class="card-img-container">
                {images_html}
            </div>
            <div class="card-content">
                <div>
                    <h2 class="title">{titre}</h2>
                    <p class="loc">📍 {loc}</p>
                </div>
                <div class="footer">
                    <div></div>
                    <div style="display:flex; flex-direction:column; align-items:flex-end;">
                        <div class="price-container" style="margin-bottom:10px;">
                            <p class="price-label">Prix Total demandé</p>
                            <p class="prix">{prix_format} FCFA</p>
                        </div>
                        <a href="{url}" class="btn" target="_blank">Voir l'offre sur Mapiole</a>
                    </div>
                </div>
            </div>
        </div>
        """
        
    html += """
        </div>
    </body>
    </html>
    """
    
    with open("resultats.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("✅ Interface générée avec succès (Style Trivago) ! Ouvrez resultats.html")

if __name__ == "__main__":
    generer_html()

