export type ProjectStatus = 'running' | 'completed' | 'failed' | 'pending';

export interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  lastRun: string;
  versions: number;
  created: string;
  description: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  agent: string;
  message: string;
}

export interface VersionEntry {
  id: string;
  version: number;
  prompt: string;
  timestamp: string;
  status: 'completed' | 'failed';
  agent: string;
}

export const projects: Project[] = [
  { id: '1', name: 'checkout-service', status: 'running', lastRun: '2 min ago', versions: 14, created: 'Jan 12, 2026', description: 'Payment checkout microservice' },
  { id: '2', name: 'auth-gateway', status: 'completed', lastRun: '1 hour ago', versions: 8, created: 'Jan 9, 2026', description: 'Authentication gateway service' },
  { id: '3', name: 'inventory-api', status: 'failed', lastRun: '3 hours ago', versions: 22, created: 'Dec 18, 2025', description: 'Inventory management REST API' },
  { id: '4', name: 'notification-worker', status: 'completed', lastRun: '6 hours ago', versions: 5, created: 'Feb 1, 2026', description: 'Background notification processing' },
  { id: '5', name: 'analytics-pipeline', status: 'pending', lastRun: 'Never', versions: 0, created: 'Feb 15, 2026', description: 'Data analytics ETL pipeline' },
  { id: '6', name: 'user-dashboard', status: 'completed', lastRun: '12 hours ago', versions: 31, created: 'Nov 3, 2025', description: 'Customer-facing dashboard UI' },
  { id: '7', name: 'billing-engine', status: 'running', lastRun: '30 sec ago', versions: 17, created: 'Dec 1, 2025', description: 'Subscription billing engine' },
  { id: '8', name: 'search-indexer', status: 'completed', lastRun: '2 days ago', versions: 9, created: 'Jan 20, 2026', description: 'Full-text search indexer service' },
];

export const pipelineAgents = [
  { id: 'pm', name: 'Requirements Agent', description: 'Understands your request', status: 'complete' as const, duration: '12s' },
  { id: 'planner', name: 'Architecture Agent', description: 'Plans the build', status: 'complete' as const, duration: '8s' },
  { id: 'engineer', name: 'Build Agent', description: 'Writes your code', status: 'running' as const, duration: '...' },
];

export const logEntries: LogEntry[] = [
  { timestamp: '14:32:01', level: 'info', agent: 'PM', message: 'Analyzing your request...' },
  { timestamp: '14:32:04', level: 'info', agent: 'PM', message: 'Requirements document created' },
  { timestamp: '14:32:05', level: 'info', agent: 'PM', message: 'Requirements verified ✓' },
  { timestamp: '14:32:06', level: 'info', agent: 'Planner', message: 'Planning the build...' },
  { timestamp: '14:32:09', level: 'info', agent: 'Planner', message: 'Created 4 build tasks' },
  { timestamp: '14:32:10', level: 'info', agent: 'Planner', message: 'Resolving build dependencies...' },
  { timestamp: '14:32:11', level: 'info', agent: 'Planner', message: 'Build plan ready — 4 files' },
  { timestamp: '14:32:12', level: 'info', agent: 'Engineer', message: 'Writing your code...' },
  { timestamp: '14:32:15', level: 'info', agent: 'Engineer', message: 'Created payment handler ✓' },
  { timestamp: '14:32:18', level: 'info', agent: 'Engineer', message: 'Created webhook handler ✓' },
  { timestamp: '14:32:20', level: 'info', agent: 'Engineer', message: 'Running quality checks...' },
  { timestamp: '14:32:22', level: 'info', agent: 'Engineer', message: 'Creating transaction model...' },
];

export const versions: VersionEntry[] = [
  { id: 'v14', version: 14, prompt: 'Add Stripe webhook handler for payment_intent.succeeded event', timestamp: 'Feb 17, 2:32 PM', status: 'completed', agent: 'engineer' },
  { id: 'v13', version: 13, prompt: 'Refactor payment service to use dependency injection pattern', timestamp: 'Feb 17, 1:15 PM', status: 'completed', agent: 'engineer' },
  { id: 'v12', version: 12, prompt: 'Add idempotency key support to all payment endpoints', timestamp: 'Feb 16, 4:45 PM', status: 'completed', agent: 'engineer' },
  { id: 'v11', version: 11, prompt: 'Fix race condition in concurrent checkout sessions', timestamp: 'Feb 16, 2:10 PM', status: 'failed', agent: 'planner' },
  { id: 'v10', version: 10, prompt: 'Implement retry logic with exponential backoff for Stripe API calls', timestamp: 'Feb 15, 11:30 AM', status: 'completed', agent: 'engineer' },
  { id: 'v9', version: 9, prompt: 'Add comprehensive error handling for payment declined scenarios', timestamp: 'Feb 14, 3:22 PM', status: 'completed', agent: 'engineer' },
  { id: 'v8', version: 8, prompt: 'Generate unit tests for PaymentProcessor class with 90% coverage', timestamp: 'Feb 13, 10:00 AM', status: 'completed', agent: 'engineer' },
];

export type FileNode = { name: string; type: 'dir'; children: FileNode[] } | { name: string; type: 'file' };

export const artifactFiles: FileNode[] = [
  { name: 'src/', type: 'dir', children: [
    { name: 'handlers/', type: 'dir', children: [
      { name: 'payment.ts', type: 'file' },
      { name: 'webhook.ts', type: 'file' },
      { name: 'refund.ts', type: 'file' },
    ]},
    { name: 'models/', type: 'dir', children: [
      { name: 'transaction.ts', type: 'file' },
      { name: 'customer.ts', type: 'file' },
    ]},
    { name: 'utils/', type: 'dir', children: [
      { name: 'stripe.ts', type: 'file' },
      { name: 'validation.ts', type: 'file' },
    ]},
    { name: 'index.ts', type: 'file' },
  ]},
];

export const sampleCode = `import Stripe from 'stripe';
import { Request, Response } from 'express';
import { TransactionModel } from '../models/transaction';
import { validatePaymentIntent } from '../utils/validation';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-12-18.acacia',
});

export class PaymentHandler {
  private transactionModel: TransactionModel;

  constructor(transactionModel: TransactionModel) {
    this.transactionModel = transactionModel;
  }

  async createCheckoutSession(req: Request, res: Response) {
    const { items, customerId, idempotencyKey } = req.body;

    try {
      const session = await stripe.checkout.sessions.create(
        {
          payment_method_types: ['card'],
          line_items: items.map((item: any) => ({
            price: item.priceId,
            quantity: item.quantity,
          })),
          mode: 'payment',
          success_url: \`\${process.env.BASE_URL}/success\`,
          cancel_url: \`\${process.env.BASE_URL}/cancel\`,
          customer: customerId,
          metadata: {
            idempotency_key: idempotencyKey,
          },
        },
        { idempotencyKey }
      );

      await this.transactionModel.create({
        sessionId: session.id,
        customerId,
        status: 'pending',
        amount: session.amount_total,
        currency: session.currency,
        createdAt: new Date(),
      });

      return res.status(200).json({
        sessionId: session.id,
        url: session.url,
      });
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        return res.status(error.statusCode ?? 500).json({
          error: error.message,
          code: error.code,
        });
      }
      throw error;
    }
  }
}`;

export const samplePRD = {
  title: "Stripe Webhook Handler Implementation",
  version: "1.0",
  author: "Archon",
  userStories: [
    "As a merchant, I want to receive real-time payment status updates so that order fulfillment is automatic.",
    "As a developer, I want idempotent webhook handling so that duplicate events don't corrupt data.",
    "As an ops engineer, I want webhook signature verification so that only authentic Stripe events are processed.",
  ],
  acceptanceCriteria: [
    "Webhook endpoint validates Stripe signature before processing",
    "payment_intent.succeeded events trigger order fulfillment",
    "payment_intent.payment_failed events update transaction status",
    "Duplicate webhook deliveries are handled idempotently",
    "Failed webhook processing triggers dead-letter queue",
    "All webhook events are logged with correlation IDs",
    "Health check endpoint returns webhook processing stats",
  ],
};

export const samplePlan = {
  modules: [
    { name: "webhook-handler", files: ["src/handlers/webhook.ts"], loc: 120, dependencies: ["stripe", "transaction-model"] },
    { name: "event-processor", files: ["src/services/event-processor.ts"], loc: 85, dependencies: ["transaction-model", "order-service"] },
    { name: "signature-verifier", files: ["src/middleware/verify-signature.ts"], loc: 45, dependencies: ["stripe"] },
    { name: "dead-letter-queue", files: ["src/services/dlq.ts"], loc: 60, dependencies: [] },
  ],
  totalLOC: 310,
  estimatedDuration: "28s",
};
