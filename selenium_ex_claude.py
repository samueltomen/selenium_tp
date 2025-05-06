import csv
import re
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

def parse_address(address_parts):
    address = " ".join(address_parts)
    match = re.search(r'(\d{5})\s*(.*)$', address)
    if match:
        code_postal = match.group(1)
        ville = match.group(2)
        rue = address.replace(f"{code_postal} {ville}", "").strip()
        return rue, code_postal, ville
    return address, "", ""

def wait_for_element(driver, by, value, timeout=20, retries=3):
    for attempt in range(retries):
        try:
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.visibility_of_element_located((by, value)))
            return element
        except (StaleElementReferenceException, TimeoutException):
            print(f"Tentative {attempt + 1}/{retries} échouée pour localiser l'élément {value}")
            if attempt == retries - 1:
                raise
            time.sleep(1)

def extraire_details_praticien(driver, url):
    """Extrait les détails d'un praticien depuis sa page personnelle"""
    driver.get(url)
    time.sleep(3)

    details = {}

    try:
        secteur_elements = driver.find_elements(By.CSS_SELECTOR, "div.dl-profile-text p")
        for elem in secteur_elements:
            if "Conventionné" in elem.text:
                details["Secteur_assurance"] = elem.text.strip()
                break
    except:
        details["Secteur_assurance"] = "Non spécifié"

    try:
        paiement_elements = driver.find_elements(By.CSS_SELECTOR, "div.dl-profile-card-content h2.dl-profile-card-title")
        for elem in paiement_elements:
            if "Moyens de paiement" in elem.text:
                parent = elem.find_element(By.XPATH, "./..")
                moyens_paiement = parent.find_element(By.CSS_SELECTOR, "div.dl-profile-text").text
                details["Moyens_paiement"] = moyens_paiement
                break
    except:
        details["Moyens_paiement"] = "Non spécifié"

    expertises = []
    try:
        expertises_elements = driver.find_elements(By.CSS_SELECTOR, "div.dl-profile-skill-chip")
        for expertise in expertises_elements:
            expertises.append(expertise.text.strip())
        details["Expertises"] = ", ".join(expertises) if expertises else "Non spécifié"
    except:
        details["Expertises"] = "Non spécifié"

    try:
        tarif_elements = driver.find_elements(By.CSS_SELECTOR, "div.dl-profile-fee")
        if tarif_elements:
            tarif = tarif_elements[0].find_element(By.CSS_SELECTOR, "span.dl-profile-fee-tag").text.strip()
            details["Prix_estime"] = tarif
    except:
        details["Prix_estime"] = "Non spécifié"

    try:
        langues_elements = driver.find_elements(By.XPATH, "//h3[contains(text(), 'Langues parlées')]/following-sibling::*")
        if langues_elements:
            details["Langues"] = langues_elements[0].text.strip()
    except:
        details["Langues"] = "Non spécifié"

    return details

today = datetime.date.today()
default_date_debut = today.strftime("%d%m%Y")
default_date_fin = (today + datetime.timedelta(days=90)).strftime("%d%m%Y")

nombre_max_input = input(f"Nombre maximum de résultats à afficher (défaut: 10) : ")
nombre_max = int(nombre_max_input) if nombre_max_input else 10

date_debut_input = input(f"Date de début (JJMMAAAA, défaut: {default_date_debut}) : ")
date_debut = date_debut_input if date_debut_input else default_date_debut

date_fin_input = input(f"Date de fin (JJMMAAAA, défaut: {default_date_fin}) : ")
date_fin = date_fin_input if date_fin_input else default_date_fin

requete_medicale_input = input("Requête médicale (ex: dermatologue, défaut: médecin généraliste) : ")
requete_medicale = requete_medicale_input if requete_medicale_input else "médecin généraliste"

type_assurance_input = input("Type d'assurance (secteur 1, secteur 2, non conventionné, défaut: secteur 1) : ")
type_assurance = type_assurance_input if type_assurance_input else "secteur 1"

type_consultation_input = input("Type de consultation (visio ou sur place, défaut: sur place) : ")
type_consultation = type_consultation_input if type_consultation_input else "sur place"

prix_min_input = input("Prix minimum (laisser vide si aucun, défaut: 0) : ")
prix_min = prix_min_input if prix_min_input else "0"

prix_max_input = input("Prix maximum (laisser vide si aucun, défaut: ∞) : ")
prix_max = prix_max_input if prix_max_input else "∞"

mot_cle_adresse_input = input("Mot-clé pour l'adresse (ex: 75015, défaut: Val de marne) : ")
mot_cle_adresse = mot_cle_adresse_input if mot_cle_adresse_input else "94"

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get("https://www.doctolib.fr")

try:
    refuse_button = wait_for_element(driver, By.ID, "didomi-notice-disagree-button")
    refuse_button.click()
except (TimeoutException, StaleElementReferenceException):
    print("Le bouton de refus des cookies n'a pas été trouvé.")

time.sleep(5)

try:
    specialite_input = wait_for_element(driver, By.CSS_SELECTOR, "input.searchbar-input.searchbar-query-input")
    specialite_input.clear()
    specialite_input.send_keys(requete_medicale)
except (TimeoutException, StaleElementReferenceException):
    print("Le champ de requête n'a pas été trouvé.")
    driver.quit()
    exit()

try:
    place_input = wait_for_element(driver, By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input")
    place_input.clear()
    place_input.send_keys(mot_cle_adresse)
    time.sleep(2)
    place_input.send_keys(Keys.ENTER)
except (TimeoutException, StaleElementReferenceException):
    print("Le champ de localisation n'a pas été trouvé.")
    driver.quit()
    exit()

time.sleep(2)

try:
    try:
        search_button = driver.find_element(By.CSS_SELECTOR, "button.searchbar-submit-button")
        driver.execute_script("arguments[0].click();", search_button)
        print("Recherche soumise via bouton (JavaScript click)")
    except:
        try:
            search_button = driver.find_element(By.XPATH, "//button[contains(@class, 'searchbar-submit')]")
            driver.execute_script("arguments[0].click();", search_button)
            print("Recherche soumise via bouton alternatif (JavaScript click)")
        except:
            place_input.send_keys(Keys.ENTER)
            print("Recherche soumise via touche Enter")
except Exception as e:
    print(f"Erreur lors de la soumission de la recherche: {str(e)}")
    print("Tentative de poursuivre malgré l'erreur...")

print("Attente du chargement des résultats...")
time.sleep(5)

if "search" in driver.current_url or "recherche" in driver.current_url or "medecin-generaliste" in driver.current_url:
    print("La page de résultats semble être chargée. URL actuelle:", driver.current_url)
else:
    print("La page de résultats ne semble pas s'être chargée correctement. URL actuelle:", driver.current_url)
    try:
        search_url = f"https://www.doctolib.fr/medecin-generaliste/{mot_cle_adresse.lower()}?ref_visit_motive_ids[]=6&ref_visit_motive_ids[]=49&ref_visit_motive_ids[]=159"
        print(f"Tentative de navigation directe vers: {search_url}")
        driver.get(search_url)
        time.sleep(5)
    except:
        print("Impossible de naviguer directement vers la page de recherche.")

print("Recherche des résultats de praticiens...")

def is_valid_practitioner(element):
    try:
        links = element.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href and any(keyword in href.lower() for keyword in ["zendesk", "article", "blog", "sante", "hc/fr", "aide", "phishing", "fraud"]):
                return False

        h2_elements = element.find_elements(By.TAG_NAME, "h2")
        if not h2_elements:
            return False

        p_elements = element.find_elements(By.TAG_NAME, "p")
        has_address_or_speciality = False
        for p in p_elements:
            text = p.text.lower()
            if "médecin" in text or "kinésithérapeute" in text or "dentiste" in text or "avenue" in text or "boulevard" in text or "rue" in text or any(cp in text for cp in ["75", "94", "93", "92", "91", "77", "78"]):
                has_address_or_speciality = True
                break

        rdv_button = element.find_elements(By.XPATH, ".//button[contains(text(), 'PRENDRE RENDEZ-VOUS')]")

        return has_address_or_speciality or len(rdv_button) > 0
    except:
        return False


print("Attente supplémentaire pour s'assurer que tous les résultats sont chargés...")
time.sleep(3)

praticien_elements = []

try:
    print("Méthode 1: Recherche par conteneur de résultats")
    results_container = driver.find_element(By.CSS_SELECTOR, ".search-results-container")
    praticien_cards = results_container.find_elements(By.CSS_SELECTOR, ".dl-search-result, .dl-card, article")
    praticien_elements.extend([card for card in praticien_cards if is_valid_practitioner(card)])
    print(f"Trouvé {len(praticien_elements)} praticiens avec la méthode 1")
except Exception as e:
    print(f"Méthode 1 échouée: {str(e)}")

if len(praticien_elements) < 2:
    try:
        print("Méthode 2: Recherche directe des cartes")
        cards = driver.find_elements(By.CSS_SELECTOR, ".dl-card, article, div[data-test-id='search-result']")
        valid_cards = [card for card in cards if is_valid_practitioner(card)]
        for card in valid_cards:
            if card not in praticien_elements:
                praticien_elements.append(card)
        print(f"Trouvé {len(praticien_elements)} praticiens après la méthode 2")
    except Exception as e:
        print(f"Méthode 2 échouée: {str(e)}")

if len(praticien_elements) < 2:
    try:
        print("Méthode 3: Recherche par noms de praticiens (h2)")
        h2_elements = driver.find_elements(By.TAG_NAME, "h2")

        for h2 in h2_elements:
            try:
                parent = h2
                for _ in range(5):  # Remonter jusqu'à 5 niveaux
                    parent = parent.find_element(By.XPATH, "..")
                    if is_valid_practitioner(parent):
                        if parent not in praticien_elements:
                            praticien_elements.append(parent)
                        break
            except:
                continue
        print(f"Trouvé {len(praticien_elements)} praticiens après la méthode 3")
    except Exception as e:
        print(f"Méthode 3 échouée: {str(e)}")

if len(praticien_elements) < 2:
    print("Tentative de navigation directe vers les profils via les URLs...")

    try:
        all_links = driver.find_elements(By.TAG_NAME, "a")
        potential_profile_urls = []

        for link in all_links:
            try:
                href = link.get_attribute("href")
                if href and ("/medecin-generaliste/" in href or "/masseur-kinesitherapeute/" in href or "/dentiste/" in href) and not any(keyword in href.lower() for keyword in ["zendesk", "article", "blog", "sante", "hc/fr", "aide", "phishing", "fraud"]):
                    potential_profile_urls.append(href)
            except:
                continue

        potential_profile_urls = list(set(potential_profile_urls))

        print(f"Trouvé {len(potential_profile_urls)} URL potentielles de profils")

        if potential_profile_urls:
            praticien_elements = []
            valid_praticien_urls = potential_profile_urls[:nombre_max]  # Limiter au nombre max
            print(f"Utilisation directe de {len(valid_praticien_urls)} URLs de profils")

            medecins = []
            seen_praticiens = set()

            for index, profile_url in enumerate(valid_praticien_urls):
                try:
                    print(f"\n--- Traitement du praticien {index+1}/{len(valid_praticien_urls)} ---")

                    print(f"Visite de la page : {profile_url}")
                    driver.get(profile_url)
                    time.sleep(3)

                    try:
                        nom = f"Praticien {index+1}"
                        try:
                            nom_elements = driver.find_elements(By.TAG_NAME, "h1")
                            if nom_elements:
                                nom = nom_elements[0].text.strip()
                            else:
                                nom_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'dl-profile-header-name')]")
                                if nom_elements:
                                    nom = nom_elements[0].text.strip()
                        except Exception as e:
                            print(f"Erreur lors de l'extraction du nom: {str(e)}")

                        print(f"Nom du praticien : {nom}")

                        rue, code_postal, ville = "Non spécifié", "Non spécifié", "Non spécifié"
                        try:
                            address_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'dl-profile-address')]")
                            if address_elements:
                                adresse_complete = address_elements[0].text.strip()
                                address_parts = adresse_complete.split('\n')
                                if len(address_parts) >= 1:
                                    rue, code_postal, ville = parse_address(address_parts)
                            else:
                                try:
                                    practice_elements = driver.find_elements(By.CSS_SELECTOR, "div.dl-profile-practice-name")
                                    if practice_elements:
                                        parent_div = practice_elements[0].find_element(By.XPATH, "./..")
                                        adresse_complete = parent_div.text.strip()

                                        address_parts = adresse_complete.split('\n')
                                        adresse_finale = address_parts[-1].strip() if len(address_parts) > 0 else adresse_complete

                                        print(f"Adresse trouvée via méthode alternative: {adresse_finale}")
                                        rue, code_postal, ville = parse_address([adresse_finale])
                                except Exception as e:
                                    print(f"Erreur lors de l'extraction alternative de l'adresse: {str(e)}")
                        except Exception as e:
                            print(f"Erreur lors de l'extraction de l'adresse: {str(e)}")

                        disponibilite = "Non disponible"
                        try:
                            disponibilite_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'dl-profile-availability')]//strong")
                            if disponibilite_elements:
                                disponibilite = disponibilite_elements[0].text.strip()
                            else:
                                disponibilite_elements = driver.find_elements(By.XPATH, "//button[contains(text(), 'Voir plus de créneaux')]")
                                if disponibilite_elements:
                                    disponibilite = "Créneaux disponibles"
                        except Exception as e:
                            print(f"Erreur lors de l'extraction des disponibilités: {str(e)}")

                        medecin = {
                            "Nom": nom,
                            "Prochaine_disponibilite": disponibilite,
                            "Type_consultation": type_consultation,
                            "Secteur_assurance": type_assurance,
                            "Prix_estime": "N/A",
                            "Rue": rue,
                            "Code_postal": code_postal,
                            "Ville": ville,
                            "Moyens_paiement": "Non spécifié",
                            "Expertises": "Non spécifié",
                            "Langues": "Non spécifié"
                        }

                        details_praticien = extraire_details_praticien(driver, profile_url)
                        medecin.update(details_praticien)

                        praticien_key = (nom, rue, code_postal)
                        if praticien_key in seen_praticiens:
                            print(f"Le praticien {nom} a déjà été traité, on l'ignore.")
                        else:
                            seen_praticiens.add(praticien_key)
                            medecins.append(medecin)
                            print(f"Informations récupérées pour {nom}")

                    except Exception as e:
                        print(f"Erreur lors de l'extraction: {str(e)}")

                    if index < len(valid_praticien_urls) - 1:
                        print("Retour à la page des résultats...")
                        driver.get(results_page_url)
                        time.sleep(3)

                except Exception as e:
                    print(f"Erreur générale pour le praticien {index+1}: {str(e)}")

            with open("medecins.csv", "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["Nom", "Prochaine_disponibilite", "Type_consultation", "Secteur_assurance",
                              "Prix_estime", "Rue", "Code_postal", "Ville", "Moyens_paiement",
                              "Expertises", "Langues"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for medecin in medecins:
                    writer.writerow(medecin)

            print(f"{len(medecins)} praticiens sauvegardés dans 'medecins.csv'")
            driver.quit()
            exit()
    except Exception as e:
        print(f"Erreur lors de la navigation directe: {str(e)}")

print(f"Nombre de praticiens trouvés au total: {len(praticien_elements)}")

if len(praticien_elements) == 0:
    print("Aucun praticien trouvé, le script s'arrête.")
    driver.quit()
    exit()

result_elements = praticien_elements[:nombre_max]
print(f"Limité à {len(result_elements)} praticiens selon le choix de l'utilisateur")

results_page_url = driver.current_url
print(f"Page de résultats : {results_page_url}")

praticien_urls = []
for index, element in enumerate(result_elements):
    print(f"Analyse de l'élément {index+1}/{len(result_elements)}")
    try:
        links = element.find_elements(By.TAG_NAME, "a")
        valid_url = None

        for link in links:
            try:
                href = link.get_attribute("href")
                if href and ("/medecin-generaliste/" in href or "/masseur-kinesitherapeute/" in href or "/dentiste/" in href) and not any(keyword in href.lower() for keyword in ["zendesk", "article", "blog", "sante", "hc/fr", "aide", "phishing", "fraud"]):
                    valid_url = href
                    break
            except:
                continue

        if valid_url:
            praticien_urls.append(valid_url)
            print(f"URL du praticien {index+1}: {valid_url}")
        else:
            print(f"Aucune URL valide trouvée pour le praticien {index+1}")
            try:
                rdv_buttons = element.find_elements(By.XPATH, ".//button[contains(text(), 'PRENDRE RENDEZ-VOUS')]")
                if rdv_buttons:
                    current_url = driver.current_url

                    driver.execute_script("arguments[0].scrollIntoView(true);", rdv_buttons[0])
                    time.sleep(1)

                    driver.execute_script("arguments[0].click();", rdv_buttons[0])
                    time.sleep(3)

                    new_url = driver.current_url
                    if new_url != current_url and not any(keyword in new_url.lower() for keyword in ["zendesk", "article", "blog", "hc/fr", "aide", "phishing", "fraud"]):
                        praticien_urls.append(new_url)
                        print(f"URL du praticien {index+1} (via clic): {new_url}")
                    else:
                        print(f"L'URL obtenue après clic n'est pas valide: {new_url}")
                        praticien_urls.append(None)

                    driver.get(results_page_url)
                    time.sleep(3)
                else:
                    praticien_urls.append(None)
            except Exception as e:
                print(f"Erreur lors de la tentative de clic: {str(e)}")
                praticien_urls.append(None)
    except Exception as e:
        print(f"Erreur lors de l'analyse de l'élément {index+1}: {str(e)}")
        praticien_urls.append(None)

valid_praticien_urls = [url for url in praticien_urls if url is not None]
print(f"URLs valides collectées: {len(valid_praticien_urls)}/{len(praticien_urls)}")

if not valid_praticien_urls:
    print("Aucune URL de praticien valide trouvée. Le script s'arrête.")
    driver.quit()
    exit()

medecins = []
seen_praticiens = set()

for index, profile_url in enumerate(valid_praticien_urls):
    try:
        print(f"\n--- Traitement du praticien {index+1}/{len(valid_praticien_urls)} ---")

        if driver.current_url != results_page_url:
            print(f"Retour à la page des résultats avant de traiter le praticien {index+1}...")
            driver.get(results_page_url)
            time.sleep(3)

        print(f"Visite de la page : {profile_url}")
        driver.get(profile_url)
        time.sleep(3)

        try:
            nom = f"Praticien {index+1}"
            try:
                nom_elements = driver.find_elements(By.TAG_NAME, "h1")
                if nom_elements:
                    nom = nom_elements[0].text.strip()
                else:
                    nom_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'dl-profile-header-name')]")
                    if nom_elements:
                        nom = nom_elements[0].text.strip()
            except Exception as e:
                print(f"Erreur lors de l'extraction du nom: {str(e)}")

            print(f"Nom du praticien : {nom}")

            rue, code_postal, ville = "Non spécifié", "Non spécifié", "Non spécifié"
            try:
                address_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'dl-profile-address')]")
                if address_elements:
                    adresse_complete = address_elements[0].text.strip()
                    address_parts = adresse_complete.split('\n')
                    if len(address_parts) >= 1:
                        rue, code_postal, ville = parse_address(address_parts)
                else:
                    try:
                        practice_elements = driver.find_elements(By.CSS_SELECTOR, "div.dl-profile-practice-name")
                        if practice_elements:
                            parent_div = practice_elements[0].find_element(By.XPATH, "./..")
                            adresse_complete = parent_div.text.strip()

                            address_parts = adresse_complete.split('\n')
                            adresse_finale = address_parts[-1].strip() if len(address_parts) > 0 else adresse_complete

                            print(f"Adresse trouvée via méthode alternative: {adresse_finale}")
                            rue, code_postal, ville = parse_address([adresse_finale])
                    except Exception as e:
                        print(f"Erreur lors de l'extraction alternative de l'adresse: {str(e)}")
            except Exception as e:
                print(f"Erreur lors de l'extraction de l'adresse: {str(e)}")

            disponibilite = "Non disponible"
            try:
                disponibilite_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'dl-profile-availability')]//strong")
                if disponibilite_elements:
                    disponibilite = disponibilite_elements[0].text.strip()
                else:
                    disponibilite_elements = driver.find_elements(By.XPATH, "//button[contains(text(), 'Voir plus de créneaux')]")
                    if disponibilite_elements:
                        disponibilite = "Créneaux disponibles"
            except Exception as e:
                print(f"Erreur lors de l'extraction des disponibilités: {str(e)}")

            medecin = {
                "Nom": nom,
                "Prochaine_disponibilite": disponibilite,
                "Type_consultation": type_consultation,
                "Secteur_assurance": type_assurance,
                "Prix_estime": "N/A",
                "Rue": rue,
                "Code_postal": code_postal,
                "Ville": ville,
                "Moyens_paiement": "Non spécifié",
                "Expertises": "Non spécifié",
                "Langues": "Non spécifié"
            }

            details_praticien = extraire_details_praticien(driver, profile_url)

            medecin.update(details_praticien)

            praticien_key = (nom, rue, code_postal)
            if praticien_key in seen_praticiens:
                print(f"Le praticien {nom} a déjà été traité, on l'ignore.")
            else:
                seen_praticiens.add(praticien_key)
                medecins.append(medecin)
                print(f"Informations récupérées pour {nom}")

        except Exception as e:
            print(f"Erreur lors de l'extraction des informations: {str(e)}")

        print("Retour à la page des résultats...")
        driver.get(results_page_url)
        time.sleep(3)

    except Exception as e:
        print(f"Erreur générale pour le praticien {index+1}: {str(e)}")
        try:
            driver.get(results_page_url)
            time.sleep(3)
        except:
            print("Impossible de revenir à la page des résultats.")

with open("medecins.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["Nom", "Prochaine_disponibilite", "Type_consultation", "Secteur_assurance",
                  "Prix_estime", "Rue", "Code_postal", "Ville", "Moyens_paiement",
                  "Expertises", "Langues"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for medecin in medecins:
        writer.writerow(medecin)

print(f"{len(medecins)} praticiens sauvegardés dans 'medecins.csv'")

driver.quit()