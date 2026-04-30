import type { MeResponse, PerfilUsuario } from '../types/contracts/auth';

export function getAvailableClientIds(user: MeResponse | null) {
  if (!user) {
    return [];
  }

  const ids = new Set(
    user.perfis
      .map((perfil) => perfil.cliente_id)
      .filter((clienteId) => clienteId !== '*'),
  );

  return [...ids];
}

export function getAvailableClients(user: MeResponse | null): { id: string; nome: string }[] {
  if (!user) return [];
  const seen = new Set<string>();
  const clients: { id: string; nome: string }[] = [];
  for (const perfil of user.perfis) {
    if (perfil.cliente_id !== '*' && !seen.has(perfil.cliente_id)) {
      seen.add(perfil.cliente_id);
      clients.push({ id: perfil.cliente_id, nome: perfil.cliente_nome ?? perfil.cliente_id });
    }
  }
  return clients;
}

export function getClientProfiles(user: MeResponse | null, clienteId: string) {
  if (!user || !clienteId) {
    return [] as PerfilUsuario[];
  }

  if (user.is_admin) {
    return ['ADMIN'];
  }

  return user.perfis
    .filter((perfil) => perfil.cliente_id === clienteId)
    .map((perfil) => perfil.perfil);
}

export function hasClienteAccess(user: MeResponse | null, clienteId: string) {
  return Boolean(clienteId) && getClientProfiles(user, clienteId).length > 0;
}

export function hasClientePerfil(
  user: MeResponse | null,
  clienteId: string,
  allowedProfiles: PerfilUsuario[],
) {
  const profiles = getClientProfiles(user, clienteId);
  return profiles.some((profile) => allowedProfiles.includes(profile));
}

export function hasAnyOperationalAccess(user: MeResponse | null) {
  return Boolean(user?.is_admin || getAvailableClientIds(user).length);
}

export function hasAdminPanelAccess(user: MeResponse | null) {
  if (!user) {
    return false;
  }

  if (user.is_admin) {
    return true;
  }

  return user.perfis.some((perfil) => perfil.perfil.trim().toUpperCase() === 'ADMIN');
}


export function hasAprovadorAccess(user: MeResponse | null) {
  if (!user) {
    return false;
  }

  if (user.is_admin) {
    return true;
  }

  return user.perfis.some((perfil) =>
    ['ADMIN', 'APROVADOR'].includes(perfil.perfil.trim().toUpperCase()),
  );
}
