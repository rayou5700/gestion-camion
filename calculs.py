from datetime import datetime, timedelta

def calculer_km(km_depart, km_arrivee):
    if km_arrivee < km_depart:
        raise ValueError("Le km d'arrivée doit être supérieur au km de départ.")
    return km_arrivee - km_depart

def estimer_carburant_restant(niveau_depart, litres_ajoutes, km_parcourus, conso_moyenne):
    litres_consommes = (km_parcourus * conso_moyenne) / 100
    restant = niveau_depart + litres_ajoutes - litres_consommes
    return max(restant, 0)

def calculer_cout_gasoil(litres_ajoutes, prix_litre):
    return litres_ajoutes * prix_litre

def get_col(t, index, default=0):
    try:
        val = t[index]
        return val if val is not None else default
    except (IndexError, TypeError):
        return default

def calculer_heures_travail(heure_debut, heure_fin):
    """Calcule la durée entre deux heures (format HH:MM)."""
    try:
        h1 = datetime.strptime(heure_debut, "%H:%M")
        h2 = datetime.strptime(heure_fin, "%H:%M")
        if h2 < h1:
            h2 += timedelta(days=1)
        delta = h2 - h1
        heures = delta.seconds / 3600
        return round(heures, 2)
    except:
        return 0

def calculer_moyennes(trajets):
    if not trajets:
        return {
            "conso": 0, "colis_transp": 0, "colis_client": 0,
            "colis_relais": 0, "colis_non_livres": 0, "taux_livraison": 0,
            "cout_total": 0, "cout_moyen_jour": 0, "total_litres": 0,
            "total_km": 0, "total_heures": 0
        }

    total_km = sum(get_col(t, 6) for t in trajets)
    total_litres = sum(get_col(t, 8) for t in trajets)
    total_transp = sum(get_col(t, 10) for t in trajets)
    total_client = sum(get_col(t, 11) for t in trajets)
    total_relais = sum(get_col(t, 12) for t in trajets)
    total_non_livres = sum(get_col(t, 13) for t in trajets)
    total_cout = sum(get_col(t, 8) * get_col(t, 9, 1.70) for t in trajets)
    total_livres = total_client + total_relais

    total_heures = 0
    for t in trajets:
        h_debut = get_col(t, 17, "")
        h_fin = get_col(t, 18, "")
        if h_debut and h_fin:
            total_heures += calculer_heures_travail(h_debut, h_fin)

    conso = (total_litres / total_km * 100) if total_km > 0 else 0
    taux = (total_livres / total_transp * 100) if total_transp > 0 else 0

    return {
        "conso": round(conso, 2),
        "colis_transp": round(total_transp / len(trajets), 1),
        "colis_client": round(total_client / len(trajets), 1),
        "colis_relais": round(total_relais / len(trajets), 1),
        "colis_non_livres": round(total_non_livres / len(trajets), 1),
        "taux_livraison": round(taux, 1),
        "cout_total": round(total_cout, 2),
        "cout_moyen_jour": round(total_cout / len(trajets), 2),
        "total_litres": round(total_litres, 1),
        "total_km": round(total_km, 1),
        "total_heures": round(total_heures, 1)
    }
