def calculer_km(km_depart, km_arrivee):
    if km_arrivee < km_depart:
        raise ValueError("Le km d'arrivée doit être supérieur au km de départ.")
    return km_arrivee - km_depart

def estimer_carburant_restant(niveau_depart, litres_ajoutes, km_parcourus, conso_moyenne):
    litres_consommes = (km_parcourus * conso_moyenne) / 100
    restant = niveau_depart + litres_ajoutes - litres_consommes
    return max(restant, 0)

def calculer_moyennes(trajets):
    if not trajets:
        return {"conso": 0, "colis_transp": 0, "colis_livres": 0, "taux_livraison": 0}

    total_km = sum(t[5] for t in trajets if t[5])
    total_litres = sum(t[7] for t in trajets if t[7])
    total_transp = sum(t[8] for t in trajets if t[8])
    total_livres = sum(t[9] for t in trajets if t[9])

    conso = (total_litres / total_km * 100) if total_km > 0 else 0
    taux = (total_livres / total_transp * 100) if total_transp > 0 else 0

    return {
        "conso": round(conso, 2),
        "colis_transp": round(total_transp / len(trajets), 1),
        "colis_livres": round(total_livres / len(trajets), 1),
        "taux_livraison": round(taux, 1)
    }
