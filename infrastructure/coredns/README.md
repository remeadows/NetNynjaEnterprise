# CoreDNS — Local DNS for GridWatch Development

CoreDNS runs as `gridwatch-coredns` on the Docker network at `172.30.0.2`.

## What it resolves

| Zone                 | Source                     | Purpose                                   |
| -------------------- | -------------------------- | ----------------------------------------- |
| `*.local.gridwatch`  | `hosts.local`              | Lab device names & Docker service aliases |
| `172.30.x.x` reverse | `hosts.local`              | PTR records for Docker network            |
| Everything else      | 8.8.8.8 / 1.1.1.1 upstream | External names (image pulls, etc.)        |

## Adding lab devices

Edit `infrastructure/coredns/hosts.local` and add entries like:

```
192.168.80.2  arista.local.gridwatch
192.168.1.1   router.local.gridwatch
```

Then restart CoreDNS:

```bash
docker compose restart coredns
```

No rebuild needed — the `hosts.local` file is bind-mounted read-only.

## Which containers use CoreDNS

The gateway (`gridwatch-gateway`) and IPAM scanner (`gridwatch-ipam-scanner`) have `dns: 172.30.0.2` set so they resolve `.local.gridwatch` names automatically. Other containers rely on Docker's built-in DNS for service-name resolution.

## Testing resolution

```bash
# From the host (uses port 5353 exposed on localhost)
nslookup arista.local.gridwatch 127.0.0.1 -port=5353

# From inside any container
docker exec gridwatch-gateway nslookup arista.local.gridwatch 172.30.0.2
```
