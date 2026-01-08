/**
 * NetNynja Enterprise - IPAM API Routes
 */

import type { FastifyPluginAsync } from "fastify";
import { z } from "zod";
import { pool } from "../../db";
import { logger } from "../../logger";

// Zod schemas
const networkSchema = z.object({
  network: z.string().regex(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/),
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  vlanId: z.number().int().min(1).max(4094).optional(),
  location: z.string().max(255).optional(),
  gateway: z.string().ip().optional(),
  site: z.string().max(255).optional(),
  isActive: z.boolean().optional(),
});

const querySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  search: z.string().optional(),
});

const ipamRoutes: FastifyPluginAsync = async (fastify) => {
  // Require authentication for all IPAM routes
  fastify.addHook("preHandler", fastify.requireAuth);

  // List networks
  fastify.get(
    "/networks",
    {
      schema: {
        tags: ["IPAM - Networks"],
        summary: "List networks",
        security: [{ bearerAuth: [] }],
        querystring: {
          type: "object",
          properties: {
            page: { type: "number", minimum: 1, default: 1 },
            limit: { type: "number", minimum: 1, maximum: 100, default: 20 },
            search: { type: "string" },
          },
        },
      },
    },
    async (request, reply) => {
      const query = querySchema.parse(request.query);
      const offset = (query.page - 1) * query.limit;

      const searchCondition = query.search
        ? `WHERE name ILIKE $3 OR network::text ILIKE $3`
        : "";
      const searchParam = query.search ? `%${query.search}%` : null;

      const countQuery = `SELECT COUNT(*) FROM ipam.networks ${searchCondition}`;
      const dataQuery = `
      SELECT id, network, name, description, vlan_id, location, site, gateway, is_active, created_at, updated_at
      FROM ipam.networks
      ${searchCondition}
      ORDER BY network
      LIMIT $1 OFFSET $2
    `;

      const params = searchParam
        ? [query.limit, offset, searchParam]
        : [query.limit, offset];

      const [countResult, dataResult] = await Promise.all([
        pool.query(countQuery, searchParam ? [searchParam] : []),
        pool.query(dataQuery, params),
      ]);

      return {
        success: true,
        data: dataResult.rows.map((row) => ({
          id: row.id,
          network: row.network,
          name: row.name,
          description: row.description,
          vlanId: row.vlan_id,
          location: row.location,
          site: row.site,
          gateway: row.gateway,
          isActive: row.is_active,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        })),
        pagination: {
          page: query.page,
          limit: query.limit,
          total: parseInt(countResult.rows[0].count, 10),
          pages: Math.ceil(
            parseInt(countResult.rows[0].count, 10) / query.limit,
          ),
        },
      };
    },
  );

  // Get network by ID
  fastify.get(
    "/networks/:id",
    {
      schema: {
        tags: ["IPAM - Networks"],
        summary: "Get network by ID",
        security: [{ bearerAuth: [] }],
        params: {
          type: "object",
          properties: {
            id: { type: "string", format: "uuid" },
          },
          required: ["id"],
        },
      },
    },
    async (request, reply) => {
      const { id } = request.params as { id: string };

      const result = await pool.query(
        `SELECT id, network, name, description, vlan_id, location, site, gateway, is_active, created_at, updated_at
       FROM ipam.networks WHERE id = $1`,
        [id],
      );

      if (result.rows.length === 0) {
        reply.status(404);
        return {
          success: false,
          error: { code: "NOT_FOUND", message: "Network not found" },
        };
      }

      const row = result.rows[0];
      return {
        success: true,
        data: {
          id: row.id,
          network: row.network,
          name: row.name,
          description: row.description,
          vlanId: row.vlan_id,
          location: row.location,
          site: row.site,
          gateway: row.gateway,
          isActive: row.is_active,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        },
      };
    },
  );

  // Create network
  fastify.post(
    "/networks",
    {
      schema: {
        tags: ["IPAM - Networks"],
        summary: "Create a new network",
        security: [{ bearerAuth: [] }],
        body: {
          type: "object",
          required: ["network", "name"],
          properties: {
            network: { type: "string" },
            name: { type: "string" },
            description: { type: "string" },
            vlanId: { type: "number" },
            location: { type: "string" },
            site: { type: "string" },
            gateway: { type: "string" },
            isActive: { type: "boolean" },
          },
        },
      },
      preHandler: [fastify.requireRole("admin", "operator")],
    },
    async (request, reply) => {
      const body = networkSchema.parse(request.body);

      const result = await pool.query(
        `INSERT INTO ipam.networks (network, name, description, vlan_id, location, site, gateway, is_active)
       VALUES ($1, $2, $3, $4, $5, $6, $7, COALESCE($8, true))
       RETURNING id, network, name, description, vlan_id, location, site, gateway, is_active, created_at, updated_at`,
        [
          body.network,
          body.name,
          body.description,
          body.vlanId,
          body.location,
          body.site,
          body.gateway,
          body.isActive,
        ],
      );

      const row = result.rows[0];
      reply.status(201);
      return {
        success: true,
        data: {
          id: row.id,
          network: row.network,
          name: row.name,
          description: row.description,
          vlanId: row.vlan_id,
          location: row.location,
          site: row.site,
          gateway: row.gateway,
          isActive: row.is_active,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        },
      };
    },
  );

  // Update network
  fastify.put(
    "/networks/:id",
    {
      schema: {
        tags: ["IPAM - Networks"],
        summary: "Update a network",
        security: [{ bearerAuth: [] }],
        params: {
          type: "object",
          properties: {
            id: { type: "string", format: "uuid" },
          },
          required: ["id"],
        },
      },
      preHandler: [fastify.requireRole("admin", "operator")],
    },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      const body = networkSchema.partial().parse(request.body);

      const updates: string[] = [];
      const values: unknown[] = [];
      let paramIndex = 1;

      if (body.network) {
        updates.push(`network = $${paramIndex++}`);
        values.push(body.network);
      }
      if (body.name) {
        updates.push(`name = $${paramIndex++}`);
        values.push(body.name);
      }
      if (body.description !== undefined) {
        updates.push(`description = $${paramIndex++}`);
        values.push(body.description);
      }
      if (body.vlanId !== undefined) {
        updates.push(`vlan_id = $${paramIndex++}`);
        values.push(body.vlanId);
      }
      if (body.location !== undefined) {
        updates.push(`location = $${paramIndex++}`);
        values.push(body.location);
      }
      if (body.site !== undefined) {
        updates.push(`site = $${paramIndex++}`);
        values.push(body.site);
      }
      if (body.gateway !== undefined) {
        updates.push(`gateway = $${paramIndex++}`);
        values.push(body.gateway);
      }
      if (body.isActive !== undefined) {
        updates.push(`is_active = $${paramIndex++}`);
        values.push(body.isActive);
      }

      if (updates.length === 0) {
        reply.status(400);
        return {
          success: false,
          error: { code: "VALIDATION_ERROR", message: "No fields to update" },
        };
      }

      values.push(id);
      const result = await pool.query(
        `UPDATE ipam.networks SET ${updates.join(", ")}, updated_at = NOW()
       WHERE id = $${paramIndex}
       RETURNING id, network, name, description, vlan_id, location, site, gateway, is_active, created_at, updated_at`,
        values,
      );

      if (result.rows.length === 0) {
        reply.status(404);
        return {
          success: false,
          error: { code: "NOT_FOUND", message: "Network not found" },
        };
      }

      const row = result.rows[0];
      return {
        success: true,
        data: {
          id: row.id,
          network: row.network,
          name: row.name,
          description: row.description,
          vlanId: row.vlan_id,
          location: row.location,
          site: row.site,
          gateway: row.gateway,
          isActive: row.is_active,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        },
      };
    },
  );

  // Delete network
  fastify.delete(
    "/networks/:id",
    {
      schema: {
        tags: ["IPAM - Networks"],
        summary: "Delete a network",
        security: [{ bearerAuth: [] }],
        params: {
          type: "object",
          properties: {
            id: { type: "string", format: "uuid" },
          },
          required: ["id"],
        },
      },
      preHandler: [fastify.requireRole("admin", "operator")],
    },
    async (request, reply) => {
      const { id } = request.params as { id: string };

      const result = await pool.query(
        "DELETE FROM ipam.networks WHERE id = $1 RETURNING id",
        [id],
      );

      if (result.rows.length === 0) {
        reply.status(404);
        return {
          success: false,
          error: { code: "NOT_FOUND", message: "Network not found" },
        };
      }

      return reply.status(204).send();
    },
  );

  // List IP addresses in a network
  fastify.get(
    "/networks/:id/addresses",
    {
      schema: {
        tags: ["IPAM - Addresses"],
        summary: "List IP addresses in a network",
        security: [{ bearerAuth: [] }],
        params: {
          type: "object",
          properties: {
            id: { type: "string", format: "uuid" },
          },
          required: ["id"],
        },
      },
    },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      const query = querySchema.parse(request.query);
      const offset = (query.page - 1) * query.limit;

      const countResult = await pool.query(
        "SELECT COUNT(*) FROM ipam.addresses WHERE network_id = $1",
        [id],
      );

      const dataResult = await pool.query(
        `SELECT id, address, hostname, fqdn, mac_address, status, device_type, description, last_seen, discovered_at, created_at, updated_at
       FROM ipam.addresses
       WHERE network_id = $1
       ORDER BY address
       LIMIT $2 OFFSET $3`,
        [id, query.limit, offset],
      );

      return {
        success: true,
        data: dataResult.rows.map((row) => ({
          id: row.id,
          address: row.address,
          hostname: row.hostname,
          fqdn: row.fqdn,
          macAddress: row.mac_address,
          status: row.status,
          deviceType: row.device_type,
          description: row.description,
          lastSeen: row.last_seen,
          discoveredAt: row.discovered_at,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        })),
        pagination: {
          page: query.page,
          limit: query.limit,
          total: parseInt(countResult.rows[0].count, 10),
          pages: Math.ceil(
            parseInt(countResult.rows[0].count, 10) / query.limit,
          ),
        },
      };
    },
  );

  // Start network scan
  fastify.post(
    "/networks/:id/scan",
    {
      schema: {
        tags: ["IPAM - Scans"],
        summary: "Start a network scan",
        security: [{ bearerAuth: [] }],
        params: {
          type: "object",
          properties: {
            id: { type: "string", format: "uuid" },
          },
          required: ["id"],
        },
        body: {
          type: "object",
          properties: {
            scanType: {
              type: "string",
              enum: ["ping", "tcp", "arp", "nmap"],
              default: "ping",
            },
          },
        },
      },
      preHandler: [fastify.requireRole("admin", "operator")],
    },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      const { scanType = "ping" } = request.body as { scanType?: string };

      // Verify network exists
      const networkResult = await pool.query(
        "SELECT id, network, name FROM ipam.networks WHERE id = $1",
        [id],
      );

      if (networkResult.rows.length === 0) {
        reply.status(404);
        return {
          success: false,
          error: { code: "NOT_FOUND", message: "Network not found" },
        };
      }

      // Create scan job
      const scanResult = await pool.query(
        `INSERT INTO ipam.scan_history (network_id, scan_type, started_at, status)
       VALUES ($1, $2, NOW(), 'pending')
       RETURNING id, network_id, scan_type, status, started_at`,
        [id, scanType],
      );

      const scan = scanResult.rows[0];

      logger.info({ networkId: id, scanId: scan.id, scanType }, "Scan started");

      return {
        success: true,
        data: {
          id: scan.id,
          networkId: scan.network_id,
          scanType: scan.scan_type,
          status: scan.status,
          startedAt: scan.started_at,
        },
        message: "Scan started",
      };
    },
  );

  // Get scan status
  fastify.get(
    "/scans/:scanId",
    {
      schema: {
        tags: ["IPAM - Scans"],
        summary: "Get scan status",
        security: [{ bearerAuth: [] }],
        params: {
          type: "object",
          properties: {
            scanId: { type: "string", format: "uuid" },
          },
          required: ["scanId"],
        },
      },
    },
    async (request, reply) => {
      const { scanId } = request.params as { scanId: string };

      const result = await pool.query(
        `SELECT id, network_id, scan_type, status, started_at, completed_at, total_ips, active_ips, new_ips, error_message
       FROM ipam.scan_history WHERE id = $1`,
        [scanId],
      );

      if (result.rows.length === 0) {
        reply.status(404);
        return {
          success: false,
          error: { code: "NOT_FOUND", message: "Scan not found" },
        };
      }

      const scan = result.rows[0];
      return {
        success: true,
        data: {
          id: scan.id,
          networkId: scan.network_id,
          scanType: scan.scan_type,
          status: scan.status,
          startedAt: scan.started_at,
          completedAt: scan.completed_at,
          totalIps: scan.total_ips,
          activeIps: scan.active_ips,
          newIps: scan.new_ips,
          errorMessage: scan.error_message,
        },
      };
    },
  );

  // List scans for a network
  fastify.get(
    "/networks/:id/scans",
    {
      schema: {
        tags: ["IPAM - Scans"],
        summary: "List scans for a network",
        security: [{ bearerAuth: [] }],
        params: {
          type: "object",
          properties: {
            id: { type: "string", format: "uuid" },
          },
          required: ["id"],
        },
      },
    },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      const query = querySchema.parse(request.query);

      const result = await pool.query(
        `SELECT id, network_id, scan_type, status, started_at, completed_at, total_ips, active_ips, new_ips
       FROM ipam.scan_history
       WHERE network_id = $1
       ORDER BY started_at DESC
       LIMIT $2`,
        [id, query.limit],
      );

      return {
        success: true,
        data: result.rows.map((scan) => ({
          id: scan.id,
          networkId: scan.network_id,
          scanType: scan.scan_type,
          status: scan.status,
          startedAt: scan.started_at,
          completedAt: scan.completed_at,
          totalIps: scan.total_ips,
          activeIps: scan.active_ips,
          newIps: scan.new_ips,
        })),
      };
    },
  );

  // IPAM Dashboard
  fastify.get(
    "/dashboard",
    {
      schema: {
        tags: ["IPAM - Dashboard"],
        summary: "Get IPAM dashboard statistics",
        security: [{ bearerAuth: [] }],
      },
    },
    async (request, reply) => {
      // Get network stats
      const networkStats = await pool.query(`
      SELECT
        COUNT(*) as total_networks,
        COUNT(*) FILTER (WHERE is_active) as active_networks
      FROM ipam.networks
    `);

      // Get address stats
      const addressStats = await pool.query(`
      SELECT
        COUNT(*) as total_addresses,
        COUNT(*) FILTER (WHERE status = 'active') as active_addresses,
        COUNT(*) FILTER (WHERE status = 'inactive') as inactive_addresses,
        COUNT(*) FILTER (WHERE status = 'reserved') as reserved_addresses
      FROM ipam.addresses
    `);

      // Get recent scans
      const recentScans = await pool.query(`
      SELECT COUNT(*) as recent_scans
      FROM ipam.scan_history
      WHERE started_at > NOW() - INTERVAL '24 hours'
    `);

      // Calculate average utilization
      const utilization = await pool.query(`
      WITH network_stats AS (
        SELECT
          n.id,
          (host(broadcast(n.network::inet)) - host(network(n.network::inet)))::int - 1 as capacity,
          COUNT(a.id) as used
        FROM ipam.networks n
        LEFT JOIN ipam.addresses a ON a.network_id = n.id
        GROUP BY n.id, n.network
      )
      SELECT
        AVG(CASE WHEN capacity > 0 THEN (used::float / capacity * 100) ELSE 0 END) as avg_utilization
      FROM network_stats
    `);

      return {
        success: true,
        data: {
          totalNetworks: parseInt(networkStats.rows[0].total_networks, 10),
          activeNetworks: parseInt(networkStats.rows[0].active_networks, 10),
          totalAddresses: parseInt(addressStats.rows[0].total_addresses, 10),
          activeAddresses: parseInt(addressStats.rows[0].active_addresses, 10),
          inactiveAddresses: parseInt(
            addressStats.rows[0].inactive_addresses,
            10,
          ),
          reservedAddresses: parseInt(
            addressStats.rows[0].reserved_addresses,
            10,
          ),
          recentScans: parseInt(recentScans.rows[0].recent_scans, 10),
          averageUtilization: parseFloat(
            utilization.rows[0].avg_utilization || 0,
          ).toFixed(2),
        },
      };
    },
  );
};

export default ipamRoutes;
