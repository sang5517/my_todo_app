def mask_email(email):
    if not email:
        return ""
    
    name, domain = email.split('@')

    if len(name) <= 2:
        masked_name = name[0] + "*"
    else:
        masked_name = name[:2] + "****"
    
    return masked_name +"@" + domain

def mask_username(username):
    if not username:
        return ""
    
    if len(username) <=2:
        return username[0] + "*"
    
    return username[:2] + "****" + username[-2:]