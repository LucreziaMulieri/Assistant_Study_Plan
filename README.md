# Assistant_Study_Plan
Project related to the creation of a web application that allows the use of a bot created using Amazon Lex.

I servizi che sono stati utilizzati per realizzarla oltre ad Amazon Lex, sono altri servizi messi a disposizione da Amazon Web Services. Tra questi sono inclusi: 
\begin{itemize}
    \item Amazon Lambda: utilizzato per la creazione di funzioni Lambda utili a gestire aspetti particolare della conversazione con utente non direttamente realizzabili tramite i soli strumenti offertati da Lex.
    \item Amazon CloudWatch: utili per la gestire la parte legata al deployment delle funzioni Lambda create, oltre a comprendere in modo accurato il flusso di conversazione del bot e la corretta integrazione delle Lambda Function.
    \item Amazon IAM: per la gestione dei permessi interni alle funzioni stesse. 
    \item Amazon Dynamo DB: ha permesso la creazione di un database NoSQL, in cui sono stati inseriti i dati relativi ai corsi opzionali offerti dall'Università Politecnica delle Marche, con l'intento di poterli richiamare durante la conversazione con l'utente, per fornire informazioni più dettagliate sui corsi stessi.
    \item Amazon CloudShell: per la gestione dei comandi da terminale, per permette la creazione del database Dynamo DB, oltre a quella della web application, sfruttando dei sample già messi a diposizione da Amazon Web Serivices (di cui si possono conoscere ulteriori inforamazioni alla documentazione Amazon), modificandoli per il caso d'uso.
    \item Amazon CloudFormation: per la gestione del deployment dell'intera infrastruttura, con la possibilità di creare un template in cui sono specificati tutti i servizi utilizzati, con le relative configurazioni, per poi effettuare il deployment in modo automatico.
\end{itemize}
