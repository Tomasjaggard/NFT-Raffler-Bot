from dataclasses import dataclass

@dataclass
class Hero:
  level: int
  image: str
  name: str
  gen: int
  prof: str
  rarity: str
  hclass: str
  hsubclass: str

@dataclass
class Gas:
  gas: int
  gasPrice: int
  maxFeePerGas: int
  maxPriorityFeePerGas: int

@dataclass
class Admin:
  guildID: int
  poolAddress: str
  poolPKey: str
  raffleAddress: str
  rafflePKey: str
  announcements: int
  logs: int
  pause: bool

@dataclass
class User:
  uID: int
  guildID: int
  address: str
  pKey: str

@dataclass
class Raffle:
  ID: int
  guildID: int
  creatorID: int
  creatorAddress: str
  nftID: int
  minTickets: int
  timeLeft: int
  ticketsSold: int
  completed: bool
  winnerID: int

@dataclass
class Entrant:
  uID: int
  entrantID: int
  address: int
  raffleID: int
  tickets: int
