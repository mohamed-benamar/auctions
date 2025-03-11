from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.auth_handler import verify_jwt_token

class JWTBearer(HTTPBearer):
    """
    Middleware pour la validation des tokens JWT dans les en-têtes d'autorisation.
    Cette classe étend HTTPBearer et vérifie la validité du token JWT fourni.
    """

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        """
        Méthode appelée pour chaque requête nécessitant une authentification.
        Vérifie le token JWT dans l'en-tête Authorization et valide sa validité.
        
        Args:
            request (Request): La requête entrante à vérifier
            
        Returns:
            str: Le token JWT valide
            
        Raises:
            HTTPException: Si le token est invalide ou absent
        """
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Schéma d'autorisation invalide. Utilisez Bearer."
                )
            
            # Vérifier la validité du token JWT
            if not verify_jwt_token(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token invalide ou expiré"
                )
                
            return credentials.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Identifiants d'autorisation invalides"
            )
