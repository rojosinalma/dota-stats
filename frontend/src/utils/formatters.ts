import { format, formatDistanceToNow } from 'date-fns'

export function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

export function formatKDA(kills: number, deaths: number, assists: number): string {
  return `${kills}/${deaths}/${assists}`
}

export function calculateKDA(kills: number, deaths: number, assists: number): number {
  if (deaths === 0) return kills + assists
  return (kills + assists) / deaths
}

export function formatNumber(num: number): string {
  return num.toLocaleString()
}

export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`
}

export function formatDate(date: string | Date): string {
  return format(new Date(date), 'MMM d, yyyy HH:mm')
}

export function formatRelativeTime(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true })
}

export function getGameModeName(gameMode: number): string {
  const modes: { [key: number]: string } = {
    0: 'Unknown',
    1: 'All Pick',
    2: 'Captain\'s Mode',
    3: 'Random Draft',
    4: 'Single Draft',
    5: 'All Random',
    6: 'Intro',
    7: 'Diretide',
    8: 'Reverse Captain\'s Mode',
    9: 'The Greeviling',
    10: 'Tutorial',
    11: 'Mid Only',
    12: 'Least Played',
    13: 'Limited Heroes',
    14: 'Compendium Matchmaking',
    15: 'Custom',
    16: 'Captain\'s Draft',
    17: 'Balanced Draft',
    18: 'Ability Draft',
    19: 'Event',
    20: 'All Random Death Match',
    21: 'Solo Mid 1v1',
    22: 'Ranked All Pick',
    23: 'Turbo',
    24: 'Mutation',
  }
  return modes[gameMode] || 'Unknown'
}

export function getLobbyTypeName(lobbyType: number): string {
  const types: { [key: number]: string } = {
    0: 'Normal',
    1: 'Practice',
    2: 'Tournament',
    3: 'Tutorial',
    4: 'Co-op Bots',
    5: 'Team Match',
    6: 'Solo Queue',
    7: 'Ranked',
    8: 'Solo Mid 1v1',
    9: 'Battle Cup',
  }
  return types[lobbyType] || 'Unknown'
}
