# Permissions

| Action | Player | Host | Captain | Venue owner | Admin |
|---|---|---|---|---|---|
| Create match | own | yes | yes | own booking only | yes |
| Edit/cancel/approve/remove | no | own match | no | linked own booking only | yes |
| Request/withdraw join | self | no normal host flow | self | self | yes |
| View private | invited/participant | own | invited | linked owner | yes |
| Result/rate | confirmed participant | own/participant | participant | no | yes |
| Manage team | member no | no | own team | no | yes |

Every object lookup derives authorization from match creator, participant, invitation or linked booking; never from client IDs.
