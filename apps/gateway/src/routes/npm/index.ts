/**
 * NetNynja Enterprise - NPM (Network Performance Monitoring) API Routes
 */

import type { FastifyPluginAsync } from "fastify";
import { z } from "zod";
import { pool } from "../../db";
import { logger } from "../../logger";
import snmpv3CredentialsRoutes from "./snmpv3-credentials";

// Zod schemas
const deviceSchema = z
  .object({
    name: z.string().min(1).max(255),
    ipAddress: z.string().ip(),
    deviceType: z.string().max(100).optional(),
    vendor: z.string().max(100).optional(),
    model: z.string().max(100).optional(),
    pollIcmp: z.boolean().default(true),
    pollSnmp: z.boolean().default(false),
    snmpv3CredentialId: z.string().uuid().optional(),
    snmpPort: z.number().int().min(1).max(65535).default(161),
    sshEnabled: z.boolean().default(false),
    pollInterval: z.number().int().min(30).max(3600).default(60),
    isActive: z.boolean().default(true),
  })
  .refine((data) => data.pollIcmp || data.pollSnmp, {
    message: "At least one polling method (ICMP or SNMP) must be enabled",
  })
  .refine(
    (data) => {
      if (data.pollSnmp) {
        return !!data.snmpv3CredentialId;
      }
      return true;
    },
    { message: "SNMPv3 credential is required when SNMP polling is enabled" },
  );

const updateDeviceSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  ipAddress: z.string().ip().optional(),
  deviceType: z.string().max(100).optional(),
  vendor: z.string().max(100).optional(),
  model: z.string().max(100).optional(),
  pollIcmp: z.boolean().optional(),
  pollSnmp: z.boolean().optional(),
  snmpv3CredentialId: z.string().uuid().nullable().optional(),
  snmpPort: z.number().int().min(1).max(65535).optional(),
  sshEnabled: z.boolean().optional(),
  pollInterval: z.number().int().min(30).max(3600).optional(),
  isActive: z.boolean().optional(),
});

const querySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  search: z.string().optional(),
  status: z.enum(["up", "down", "unknown"]).optional(),
});

const metricsQuerySchema = z.object({
  startTime: z.coerce.date().optional(),
  endTime: z.coerce.date().optional(),
  metricType: z
    .enum(["cpu", "memory", "bandwidth", "latency", "packet_loss"])
    .optional(),
});

const npmRoutes: FastifyPluginAsync = async (fastify) => {
  // Register SNMPv3 credentials routes
  await fastify.register(snmpv3CredentialsRoutes, {
    prefix: "/snmpv3-credentials",
  });

  // Require authentication for all NPM routes
  fastify.addHook("preHandler", fastify.requireAuth);

  // List monitored devices
  fastify.get(
    "/devices",
    {
      schema: {
        tags: ["NPM - Devices"],
        summary: "List monitored devices",
        security: [{ bearerAuth: [] }],
        querystring: {
          type: "object",
          properties: {
            page: { type: "number", minimum: 1, default: 1 },
            limit: { type: "number", minimum: 1, maximum: 100, default: 20 },
            search: { type: "string" },
            status: { type: "string", enum: ["up", "down", "unknown"] },
          },
        },
      },
    },
    async (request, reply) => {
      const query = querySchema.parse(request.query);
      const offset = (query.page - 1) * query.limit;

      const conditions: string[] = [];
      const params: unknown[] = [query.limit, offset];
      let paramIndex = 3;

      if (query.search) {
        conditions.push(
          `(d.name ILIKE $${paramIndex} OR d.ip_address::text ILIKE $${paramIndex})`,
        );
        params.push(`%${query.search}%`);
        paramIndex++;
      }
      if (query.status) {
        conditions.push(`d.status = $${paramIndex}`);
        params.push(query.status);
        paramIndex++;
      }

      const whereClause =
        conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

      const countQuery = `SELECT COUNT(*) FROM npm.devices d ${whereClause}`;
      const dataQuery = `
      SELECT d.id, d.name, d.ip_address, d.device_type, d.vendor, d.model, d.status,
             d.poll_icmp, d.poll_snmp, d.snmpv3_credential_id, c.name as snmpv3_credential_name,
             d.snmp_port, d.ssh_enabled, d.poll_interval, d.is_active,
             d.last_poll, d.last_icmp_poll, d.last_snmp_poll,
             d.icmp_status, d.snmp_status, d.created_at, d.updated_at
      FROM npm.devices d
      LEFT JOIN npm.snmpv3_credentials c ON d.snmpv3_credential_id = c.id
      ${whereClause}
      ORDER BY d.name
      LIMIT $1 OFFSET $2
    `;

      const [countResult, dataResult] = await Promise.all([
        pool.query(countQuery, params.slice(2)),
        pool.query(dataQuery, params),
      ]);

      return {
        success: true,
        data: dataResult.rows.map((row) => ({
          id: row.id,
          name: row.name,
          ipAddress: row.ip_address,
          deviceType: row.device_type,
          vendor: row.vendor,
          model: row.model,
          status: row.status,
          pollIcmp: row.poll_icmp,
          pollSnmp: row.poll_snmp,
          snmpv3CredentialId: row.snmpv3_credential_id,
          snmpv3CredentialName: row.snmpv3_credential_name,
          snmpPort: row.snmp_port,
          sshEnabled: row.ssh_enabled,
          pollInterval: row.poll_interval,
          isActive: row.is_active,
          lastPoll: row.last_poll,
          lastIcmpPoll: row.last_icmp_poll,
          lastSnmpPoll: row.last_snmp_poll,
          icmpStatus: row.icmp_status,
          snmpStatus: row.snmp_status,
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

  // Get device by ID
  fastify.get(
    "/devices/:id",
    {
      schema: {
        tags: ["NPM - Devices"],
        summary: "Get device by ID",
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
        `SELECT d.id, d.name, d.ip_address, d.device_type, d.vendor, d.model, d.status,
              d.poll_icmp, d.poll_snmp, d.snmpv3_credential_id, c.name as snmpv3_credential_name,
              d.snmp_port, d.ssh_enabled, d.poll_interval, d.is_active,
              d.last_poll, d.last_icmp_poll, d.last_snmp_poll,
              d.icmp_status, d.snmp_status, d.created_at, d.updated_at
       FROM npm.devices d
       LEFT JOIN npm.snmpv3_credentials c ON d.snmpv3_credential_id = c.id
       WHERE d.id = $1`,
        [id],
      );

      if (result.rows.length === 0) {
        reply.status(404);
        return {
          success: false,
          error: { code: "NOT_FOUND", message: "Device not found" },
        };
      }

      const row = result.rows[0];
      return {
        success: true,
        data: {
          id: row.id,
          name: row.name,
          ipAddress: row.ip_address,
          deviceType: row.device_type,
          vendor: row.vendor,
          model: row.model,
          status: row.status,
          pollIcmp: row.poll_icmp,
          pollSnmp: row.poll_snmp,
          snmpv3CredentialId: row.snmpv3_credential_id,
          snmpv3CredentialName: row.snmpv3_credential_name,
          snmpPort: row.snmp_port,
          sshEnabled: row.ssh_enabled,
          pollInterval: row.poll_interval,
          isActive: row.is_active,
          lastPoll: row.last_poll,
          lastIcmpPoll: row.last_icmp_poll,
          lastSnmpPoll: row.last_snmp_poll,
          icmpStatus: row.icmp_status,
          snmpStatus: row.snmp_status,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        },
      };
    },
  );

  // Create device
  fastify.post(
    "/devices",
    {
      schema: {
        tags: ["NPM - Devices"],
        summary: "Add a new device to monitoring",
        description:
          "Add a device with ICMP, SNMPv3, or both polling methods enabled.",
        security: [{ bearerAuth: [] }],
        body: {
          type: "object",
          required: ["name", "ipAddress"],
          properties: {
            name: { type: "string" },
            ipAddress: { type: "string" },
            deviceType: { type: "string" },
            vendor: { type: "string" },
            model: { type: "string" },
            pollIcmp: { type: "boolean", default: true },
            pollSnmp: { type: "boolean", default: false },
            snmpv3CredentialId: { type: "string", format: "uuid" },
            snmpPort: { type: "number", default: 161 },
            sshEnabled: { type: "boolean" },
            pollInterval: { type: "number" },
            isActive: { type: "boolean" },
          },
        },
      },
      preHandler: [fastify.requireRole("admin", "operator")],
    },
    async (request, reply) => {
      const body = deviceSchema.parse(request.body);

      // If SNMPv3 credential ID is provided, verify it exists
      if (body.snmpv3CredentialId) {
        const credCheck = await pool.query(
          "SELECT id FROM npm.snmpv3_credentials WHERE id = $1",
          [body.snmpv3CredentialId],
        );
        if (credCheck.rows.length === 0) {
          reply.status(400);
          return {
            success: false,
            error: {
              code: "BAD_REQUEST",
              message: "SNMPv3 credential not found",
            },
          };
        }
      }

      const result = await pool.query(
        `INSERT INTO npm.devices (name, ip_address, device_type, vendor, model, poll_icmp, poll_snmp,
                                snmpv3_credential_id, snmp_port, ssh_enabled, poll_interval, is_active)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
       RETURNING id, name, ip_address, device_type, vendor, model, status,
                 poll_icmp, poll_snmp, snmpv3_credential_id, snmp_port,
                 ssh_enabled, poll_interval, is_active, created_at, updated_at`,
        [
          body.name,
          body.ipAddress,
          body.deviceType,
          body.vendor,
          body.model,
          body.pollIcmp,
          body.pollSnmp,
          body.snmpv3CredentialId,
          body.snmpPort,
          body.sshEnabled,
          body.pollInterval,
          body.isActive,
        ],
      );

      const row = result.rows[0];
      reply.status(201);
      return {
        success: true,
        data: {
          id: row.id,
          name: row.name,
          ipAddress: row.ip_address,
          deviceType: row.device_type,
          vendor: row.vendor,
          model: row.model,
          status: row.status,
          pollIcmp: row.poll_icmp,
          pollSnmp: row.poll_snmp,
          snmpv3CredentialId: row.snmpv3_credential_id,
          snmpPort: row.snmp_port,
          sshEnabled: row.ssh_enabled,
          pollInterval: row.poll_interval,
          isActive: row.is_active,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        },
      };
    },
  );

  // Update device
  fastify.patch(
    "/devices/:id",
    {
      schema: {
        tags: ["NPM - Devices"],
        summary: "Update a monitored device",
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
            name: { type: "string" },
            ipAddress: { type: "string" },
            deviceType: { type: "string" },
            vendor: { type: "string" },
            model: { type: "string" },
            pollIcmp: { type: "boolean" },
            pollSnmp: { type: "boolean" },
            snmpv3CredentialId: {
              type: "string",
              format: "uuid",
              nullable: true,
            },
            snmpPort: { type: "number" },
            sshEnabled: { type: "boolean" },
            pollInterval: { type: "number" },
            isActive: { type: "boolean" },
          },
        },
      },
      preHandler: [fastify.requireRole("admin", "operator")],
    },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      const body = updateDeviceSchema.parse(request.body);

      // Check if device exists
      const existingResult = await pool.query(
        "SELECT id, poll_icmp, poll_snmp FROM npm.devices WHERE id = $1",
        [id],
      );

      if (existingResult.rows.length === 0) {
        reply.status(404);
        return {
          success: false,
          error: { code: "NOT_FOUND", message: "Device not found" },
        };
      }

      // Validate polling methods
      const existing = existingResult.rows[0];
      const newPollIcmp = body.pollIcmp ?? existing.poll_icmp;
      const newPollSnmp = body.pollSnmp ?? existing.poll_snmp;

      if (!newPollIcmp && !newPollSnmp) {
        reply.status(400);
        return {
          success: false,
          error: {
            code: "BAD_REQUEST",
            message: "At least one polling method must be enabled",
          },
        };
      }

      // If SNMPv3 credential ID is provided, verify it exists
      if (body.snmpv3CredentialId) {
        const credCheck = await pool.query(
          "SELECT id FROM npm.snmpv3_credentials WHERE id = $1",
          [body.snmpv3CredentialId],
        );
        if (credCheck.rows.length === 0) {
          reply.status(400);
          return {
            success: false,
            error: {
              code: "BAD_REQUEST",
              message: "SNMPv3 credential not found",
            },
          };
        }
      }

      // Build update query dynamically
      const updates: string[] = [];
      const params: unknown[] = [];
      let paramIndex = 1;

      if (body.name !== undefined) {
        updates.push(`name = $${paramIndex++}`);
        params.push(body.name);
      }
      if (body.ipAddress !== undefined) {
        updates.push(`ip_address = $${paramIndex++}`);
        params.push(body.ipAddress);
      }
      if (body.deviceType !== undefined) {
        updates.push(`device_type = $${paramIndex++}`);
        params.push(body.deviceType);
      }
      if (body.vendor !== undefined) {
        updates.push(`vendor = $${paramIndex++}`);
        params.push(body.vendor);
      }
      if (body.model !== undefined) {
        updates.push(`model = $${paramIndex++}`);
        params.push(body.model);
      }
      if (body.pollIcmp !== undefined) {
        updates.push(`poll_icmp = $${paramIndex++}`);
        params.push(body.pollIcmp);
      }
      if (body.pollSnmp !== undefined) {
        updates.push(`poll_snmp = $${paramIndex++}`);
        params.push(body.pollSnmp);
      }
      if (body.snmpv3CredentialId !== undefined) {
        updates.push(`snmpv3_credential_id = $${paramIndex++}`);
        params.push(body.snmpv3CredentialId);
      }
      if (body.snmpPort !== undefined) {
        updates.push(`snmp_port = $${paramIndex++}`);
        params.push(body.snmpPort);
      }
      if (body.sshEnabled !== undefined) {
        updates.push(`ssh_enabled = $${paramIndex++}`);
        params.push(body.sshEnabled);
      }
      if (body.pollInterval !== undefined) {
        updates.push(`poll_interval = $${paramIndex++}`);
        params.push(body.pollInterval);
      }
      if (body.isActive !== undefined) {
        updates.push(`is_active = $${paramIndex++}`);
        params.push(body.isActive);
      }

      if (updates.length === 0) {
        reply.status(400);
        return {
          success: false,
          error: { code: "BAD_REQUEST", message: "No fields to update" },
        };
      }

      params.push(id);
      const result = await pool.query(
        `UPDATE npm.devices
       SET ${updates.join(", ")}
       WHERE id = $${paramIndex}
       RETURNING id, name, ip_address, device_type, vendor, model, status,
                 poll_icmp, poll_snmp, snmpv3_credential_id, snmp_port,
                 ssh_enabled, poll_interval, is_active, created_at, updated_at`,
        params,
      );

      const row = result.rows[0];
      return {
        success: true,
        data: {
          id: row.id,
          name: row.name,
          ipAddress: row.ip_address,
          deviceType: row.device_type,
          vendor: row.vendor,
          model: row.model,
          status: row.status,
          pollIcmp: row.poll_icmp,
          pollSnmp: row.poll_snmp,
          snmpv3CredentialId: row.snmpv3_credential_id,
          snmpPort: row.snmp_port,
          sshEnabled: row.ssh_enabled,
          pollInterval: row.poll_interval,
          isActive: row.is_active,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        },
      };
    },
  );

  // Delete device
  fastify.delete(
    "/devices/:id",
    {
      schema: {
        tags: ["NPM - Devices"],
        summary: "Remove device from monitoring",
        security: [{ bearerAuth: [] }],
        params: {
          type: "object",
          properties: {
            id: { type: "string", format: "uuid" },
          },
          required: ["id"],
        },
      },
      preHandler: [fastify.requireRole("admin")],
    },
    async (request, reply) => {
      const { id } = request.params as { id: string };

      const result = await pool.query(
        "DELETE FROM npm.devices WHERE id = $1 RETURNING id",
        [id],
      );

      if (result.rows.length === 0) {
        reply.status(404);
        return {
          success: false,
          error: { code: "NOT_FOUND", message: "Device not found" },
        };
      }

      reply.status(204).send();
    },
  );

  // Get device metrics
  // NOTE: Metrics are stored in VictoriaMetrics, not PostgreSQL
  // This endpoint provides a placeholder until VictoriaMetrics integration is complete
  fastify.get(
    "/devices/:id/metrics",
    {
      schema: {
        tags: ["NPM - Metrics"],
        summary:
          "Get metrics for a device (VictoriaMetrics integration pending)",
        security: [{ bearerAuth: [] }],
        params: {
          type: "object",
          properties: {
            id: { type: "string", format: "uuid" },
          },
          required: ["id"],
        },
        querystring: {
          type: "object",
          properties: {
            startTime: { type: "string", format: "date-time" },
            endTime: { type: "string", format: "date-time" },
            metricType: {
              type: "string",
              enum: ["cpu", "memory", "bandwidth", "latency", "packet_loss"],
            },
          },
        },
      },
    },
    async (request, reply) => {
      const { id } = request.params as { id: string };
      const query = metricsQuerySchema.parse(request.query);

      // Verify device exists
      const deviceResult = await pool.query(
        "SELECT id, name FROM npm.devices WHERE id = $1",
        [id],
      );

      if (deviceResult.rows.length === 0) {
        reply.status(404);
        return {
          success: false,
          error: { code: "NOT_FOUND", message: "Device not found" },
        };
      }

      // Default to last hour
      const endTime = query.endTime || new Date();
      const startTime =
        query.startTime || new Date(endTime.getTime() - 3600000);

      // TODO: Integrate with VictoriaMetrics for actual metrics
      // For now, return empty metrics array
      return {
        success: true,
        data: {
          deviceId: id,
          deviceName: deviceResult.rows[0].name,
          startTime: startTime.toISOString(),
          endTime: endTime.toISOString(),
          metrics: [],
          _note:
            "VictoriaMetrics integration pending - metrics will be available once collectors are running",
        },
      };
    },
  );

  // List alerts
  fastify.get(
    "/alerts",
    {
      schema: {
        tags: ["NPM - Alerts"],
        summary: "List active alerts",
        security: [{ bearerAuth: [] }],
        querystring: {
          type: "object",
          properties: {
            page: { type: "number", minimum: 1, default: 1 },
            limit: { type: "number", minimum: 1, maximum: 100, default: 20 },
            severity: { type: "string", enum: ["critical", "warning", "info"] },
            status: {
              type: "string",
              enum: ["active", "acknowledged", "resolved"],
            },
          },
        },
      },
    },
    async (request, reply) => {
      const query = querySchema.parse(request.query);
      const offset = (query.page - 1) * query.limit;

      const result = await pool.query(
        `SELECT a.id, a.device_id, d.name as device_name, a.severity, a.message, a.status,
              a.details, a.acknowledged_by, a.acknowledged_at, a.triggered_at, a.resolved_at
       FROM npm.alerts a
       LEFT JOIN npm.devices d ON a.device_id = d.id
       WHERE a.status = 'active'
       ORDER BY
         CASE a.severity
           WHEN 'critical' THEN 1
           WHEN 'warning' THEN 2
           ELSE 3
         END,
         a.triggered_at DESC
       LIMIT $1 OFFSET $2`,
        [query.limit, offset],
      );

      return {
        success: true,
        data: result.rows.map((row) => ({
          id: row.id,
          deviceId: row.device_id,
          deviceName: row.device_name,
          severity: row.severity,
          message: row.message,
          status: row.status,
          details: row.details,
          acknowledgedBy: row.acknowledged_by,
          acknowledgedAt: row.acknowledged_at,
          triggeredAt: row.triggered_at,
          resolvedAt: row.resolved_at,
        })),
      };
    },
  );
};

export default npmRoutes;
