<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            // 改名 credit_amount → pulse_to_display（保留現有資料）
            $table->renameColumn('credit_amount', 'pulse_to_display');
        });

        Schema::table('devices', function (Blueprint $table) {
            // 移除舊參數欄位（DB 實際存在這三個欄位）
            $table->dropColumn(['pulse_ratio', 'score_to_money_rate', 'coin_to_score_rate']);
        });

        Schema::table('devices', function (Blueprint $table) {
            // 新增出金模式欄位
            $table->enum('ticket_mode', ['virtual_ticket', 'physical_ticket', 'direct_prize'])
                ->nullable()
                ->after('pulse_to_display')
                ->comment('出金模式');

            $table->unsignedInteger('out_pulse_to_ticket')
                ->nullable()
                ->after('ticket_mode')
                ->comment('出金計數器跳1下=幾張彩票');

            $table->unsignedInteger('ticket_value')
                ->nullable()
                ->after('out_pulse_to_ticket')
                ->comment('1張彩票的法幣價值（元/張），統計用');

            $table->unsignedInteger('direct_prize_cost')
                ->nullable()
                ->after('ticket_value')
                ->comment('出金計數器跳1下的實體耗損（元/下）');
        });
    }

    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->dropColumn(['ticket_mode', 'out_pulse_to_ticket', 'ticket_value', 'direct_prize_cost']);
        });

        Schema::table('devices', function (Blueprint $table) {
            $table->integer('pulse_ratio')->nullable()->after('type_id');
            $table->decimal('score_to_money_rate', 10, 4)->nullable()->after('pulse_ratio');
            $table->integer('coin_to_score_rate')->nullable()->after('score_to_money_rate');
        });

        Schema::table('devices', function (Blueprint $table) {
            $table->renameColumn('pulse_to_display', 'credit_amount');
        });
    }
};
