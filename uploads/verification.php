 <?php
if ($_SERVER["REQUEST_METHOD"] == "GET") {
    $erreurs = [];

    // Récupération et validation des champs
    $nom = trim($_GET['nom']);
    $prenom = trim($_GET['prenom']);
    $email = trim($_GET['email']);
    $age = trim($_GET['age']);
    $motdepasse = trim($_GET['motdepasse']);
    $confirmemotdepasse = trim($_GET['confirmemotdepasse']);

    if (empty($nom)) {
        $erreurs['nom'] = "Veuillez remplir le champ nom.";
    }

    if (empty($prenom)) {
        $erreurs['prenom'] = "Veuillez remplir le champ prénom.";
    }

    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $erreurs['email'] = "Veuillez entrer un email valide.";
    }

    if (!is_numeric($age)) {
        $erreurs['age'] = "Veuillez entrer une valeur numérique pour l'âge.";
    }

    if (strlen($motdepasse) < 6) {
        $erreurs['motdepasse'] = "Le mot de passe doit contenir au moins 6 caractères.";
    }

    if ($motdepasse !== $confirmemotdepasse) {
        $erreurs['confirmemotdepasse'] = "La confirmation du mot de passe ne correspond pas.";
    }

    // Afficher les erreurs ou traiter les données
    if (!empty($erreurs)) {
        foreach ($erreurs as $champ => $message) {
            echo "<p style='color: red;'>Erreur ($champ) : $message</p>";
        }
    } else {
        echo "<p style='color: green;'>Formulaire validé avec succès !</p>";
        // Traitez ici les données comme l'insertion dans une base de données
    }
}
?>