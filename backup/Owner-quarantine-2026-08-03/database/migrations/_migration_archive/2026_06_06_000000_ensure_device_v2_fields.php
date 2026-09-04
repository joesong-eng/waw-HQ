<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            if (!Schema::hasColumn('devices', 'ticket_mode')) {
                $table->enum('ticket_mode', ['virtual_ticket', 'physical_ticket', 'direct_prize'])
                    ->nullable()
                    ->after('pulse_to_display')
                    ->comment('出金模式');
            }
            if (!Schema::hasColumn('devices', 'out_pulse_to_ticket')) {
                $table->unsignedInteger('out_pulse_to_ticket')
                    ->nullable()
                    ->after('ticket_mode')
                    ->comment('出金計數器跳1下=幾張彩票');
            }
            if (!Schema::hasColumn('devices', 'ticket_value')) {
                $table->unsignedInteger('ticket_value')
                    ->nullable()
                    ->after('out_pulse_to_ticket')
                    ->comment('1張彩票的法幣價值（元/張），統計用');
            }
            if (!Schema::hasColumn('devices', 'direct_prize_cost')) {
                $table->unsignedInteger('direct_prize_cost')
                    ->nullable()
                    ->after('ticket_value')
                    ->comment('出金計數器跳1下的實體耗損（元/下）');
            }
        });
    }

    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $columns = [];
            if (Schema::hasColumn('devices', 'ticket_mode')) {
                $columns[] = 'ticket_mode';
            }
            if (Schema::hasColumn('devices', 'out_pulse_to_ticket')) {
                $columns[] = 'out_pulse_to_ticket';
            }
            if (Schema::hasColumn('devices', 'ticket_value')) {
                $columns[] = 'ticket_value';
            }
            if (Schema::hasColumn('devices', 'direct_prize_cost')) {
                $columns[] = 'direct_prize_cost';
            }
            if (!empty($columns)) {
                $table->dropColumn($columns);
            }
        });
    }
};
