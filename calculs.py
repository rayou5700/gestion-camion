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

def calculer_moyennes(trajets):
    if not trajets:
        return {
            "conso": 0, "colis_transp": 0, "colis_client": 0,
            "colis_relais": 0, "taux_livraison": 0, "cout_total": 0,
            "cout_moyen_jour": 0, "total_litres": 0, "total_km": 0
        }

    total_km = sum(t[6] for t in trajets if t[6])
    total_litres = sum(t[8] for t in trajets if t[8])
    total_transp = sum(t[10] for t in trajets if t[10])
    total_client = sum(t[11] for t in trajets if t[11])
    total_relais = sum(t[12] for t in trajets if t[12])
    total_cout = sum((t[8] or 0) * (t[9] or 0) for t in trajets)
    total_livres = total_client + total_relais

    conso = (total_litres / total_km * 100) if total_km > 0 else 0
    taux = (total_livres / total_transp * 100) if total_transp > 0 else 0

    return {
        "conso": round(conso, 2),
        "colis_transp": round(total_transp / len(trajets), 1),
        "colis_client": round(total_client / len(trajets), 1),
        "colis_relais": round(total_relais / len(trajets), 1),
        "taux_livraison": round(taux, 1),
        "cout_total": round(total_cout, 2),
        "cout_moyen_jour": round(total_cout / len(trajets), 2),
        "total_litres": round(total_litres, 1),
        "total_km": round(total_km, 1)
    }
