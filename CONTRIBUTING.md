# Contributing

This repository is public so anyone can **read and fork**.

Forks are yours. You may copy, study, and build on a fork under the license.

You cannot write the in-house copies:

- `The-ChristmanAI-Project/Harvest-Now-Decrypt-Later`
- `EverettNC/Harvest-Now-Decrypt-Later`

Pull requests are proposals. They do not land unless Everett Christman (`EverettNC`) merges them. A PR that adds an unused backend, a status slogan, or a dependency the seal path does not call will be closed.

The Harvest Now, Decrypt Later seal is Python ML-KEM-768 in `christman_crypto/postquantum.py`. That is the lock. Do not "harden" it with a crate that is not on the encrypt/decrypt path.
