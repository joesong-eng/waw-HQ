<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('settlements', function (Blueprint $table) {
            $table->decimal('pre_tax_expenses', 12, 2)->default(0)->after('total_revenue')->comment('飛帳扣除');
            $table->decimal('taxable_revenue', 12, 2)->default(0)->after('pre_tax_expenses')->comment('應納稅/分潤額 (Revenue - Expenses)');
            $table->json('device_breakdown')->nullable()->after('taxable_revenue')->comment('機台細項分解');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('settlements', function (Blueprint $table) {
            $table->dropColumn(['pre_tax_expenses', 'taxable_revenue', 'device_breakdown']);
        });
    }
};
